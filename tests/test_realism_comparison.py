import json
import re
from pathlib import Path
import pytest

REQUIRED_KEYS = [
    "patients",
    "recordings",
    "observed_samples",
    "total_slots",
    "gap_stats_15m",
    "gap_stats_5m",
    "meal_rise_mean",
    "mean_glucose",
    "std_glucose",
    "cv_glucose",
    "time_below_70",
    "time_70_180",
    "time_above_180",
    "age",
    "bmi",
    "hba1c",
    "insulin_use",
    "hour_profile",
    "label_prevalence",
    "regression_hba1c_glucose"
]

def test_realism_comparison_keys_and_structure():
    path = Path("reports/realism_comparison.json")
    assert path.exists(), "reports/realism_comparison.json must exist"
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Assert all required top-level keys
    for k in REQUIRED_KEYS:
        assert k in data, f"Missing required top-level key: {k}"

    # 2. Check counts and slot metrics
    assert "real" in data["patients"] and "synthetic" in data["patients"]
    assert "real" in data["recordings"] and "synthetic" in data["recordings"]
    assert "real" in data["observed_samples"] and "synthetic" in data["observed_samples"]
    assert "real" in data["total_slots"] and "synthetic" in data["total_slots"]

    # 3. Check time in ranges have both patient-level average and pooled share
    for range_key in ["time_below_70", "time_70_180", "time_above_180"]:
        sub = data[range_key]
        assert "real" in sub, f"{range_key} missing 'real'"
        assert "synthetic" in sub, f"{range_key} missing 'synthetic'"
        assert "real_pooled" in sub, f"{range_key} missing 'real_pooled'"
        assert "synthetic_pooled" in sub, f"{range_key} missing 'synthetic_pooled'"

    # 4. Check hour-of-day profile
    assert len(data["hour_profile"]["real"]) == 24
    assert len(data["hour_profile"]["synthetic"]) == 24

    # 5. Check gap statistics
    assert "gaps_per_1000_slots" in data["gap_stats_15m"]["real"]
    assert "gaps_per_1000_slots" in data["gap_stats_15m"]["synthetic"]

    # 6. Check HbA1c regression
    assert "slope" in data["regression_hba1c_glucose"]["real"]
    assert "slope" in data["regression_hba1c_glucose"]["synthetic"]


def test_readme_cohort_numbers_match_realism_file():
    realism_path = Path("reports/realism_comparison.json")
    readme_path = Path("README.md")
    assert realism_path.exists()
    assert readme_path.exists()

    with open(realism_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    readme_content = readme_path.read_text(encoding="utf-8")

    synth_mean_str = f"{data['mean_glucose']['synthetic']:.2f}"
    real_mean_str = f"{data['mean_glucose']['real']:.2f}"
    synth_tar_str = f"{data['time_above_180']['synthetic']*100:.1f}%"
    real_tar_str = f"{data['time_above_180']['real']*100:.1f}%"

    # Expected exact numbers
    assert synth_mean_str == "219.30"
    assert real_mean_str == "141.01"
    assert synth_tar_str == "68.6%"
    assert real_tar_str == "19.6%"

    # Assert these exact formatted numbers are present in the README cohort comparison
    assert f"mean glucose is {synth_mean_str} mg/dL in synthetic vs {real_mean_str} mg/dL in the real cohort" in readme_content
    assert f"time above 180 (patient-level average) is {synth_tar_str} in synthetic vs {real_tar_str} in the real cohort" in readme_content


def test_real_values_match_real_range_check():
    realism_path = Path("reports/realism_comparison.json")
    rc_path = Path("reports/real_range_check.json")
    assert realism_path.exists()
    assert rc_path.exists()

    with open(realism_path, "r", encoding="utf-8") as f:
        realism = json.load(f)
    with open(rc_path, "r", encoding="utf-8") as f:
        rc = json.load(f)

    # Real patient-level mean: 141.01
    assert round(realism["mean_glucose"]["real"], 2) == 141.01
    assert float(rc["patient_level_mean_glucose"]["with_floor"]) == 141.01

    # Time below 70: 0.0253
    assert round(realism["time_below_70"]["real"], 4) == 0.0253
    assert float(rc["time_below_70_with_floor"]["per_patient"]) == 0.0253

    # Time above 180 (patient-level average): 0.1963
    assert round(realism["time_above_180"]["real"], 4) == 0.1963
    assert float(rc["candidate_range_details"]["39 to 501"]["time_above_180_per_patient"]) == 0.1963

    # Time above 180 (pooled share): 0.1890
    assert round(realism["time_above_180"]["real_pooled"], 4) == 0.1890
    assert float(rc["candidate_range_details"]["39 to 501"]["time_above_180_pooled"]) == 0.1890
