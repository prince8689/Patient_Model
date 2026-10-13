import ast
from datetime import datetime, timedelta
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.app_lib.user_input import (
    validate_profile, validate_time, validate_glucose, 
    validate_meals_exercise, build_frame, evaluate_tier,
    run_indicative_path, run_full_path, get_provided_summary,
    get_cohort_comparison_statement, get_sensitivity_statement,
    get_confidence_label
)

def test_validation_ranges():
    now = datetime(2024, 1, 1, 12, 0)
    
    # Profile
    p_err, e = validate_profile({"age": "10", "bmi": "100", "hba1c": "20"})
    assert "Age must be between 18 and 90." in e
    assert "BMI must be between 15 and 60." in e
    assert "HbA1c must be between 4 and 15 percent." in e
    
    # Time
    dt, err = validate_time("2024-01-01 13:00", now)
    assert "in the future" in err[0]
    dt, err = validate_time(-10, now)
    assert "in the future" in err[0]
    
    # Glucose
    _, err = validate_glucose([{"time": "0", "value": "30"}], now)
    assert any("outside the valid range" in x for x in err)
    _, err = validate_glucose([{"time": "0", "value": "510"}], now)
    assert any("outside the valid range" in x for x in err)
    
    # Units
    v, err = validate_glucose([{"time": "0", "value": "10", "unit": "mmol/L"}], now)
    assert len(err) == 0
    assert abs(v[0]["glucose_mgdl"] - 180.16) < 1e-4

def test_frame_schema_and_alignment():
    now = datetime(2024, 1, 1, 12, 1)
    readings = [{"timestamp": datetime(2024, 1, 1, 12, 1), "glucose_mgdl": 100}]
    df, adj = build_frame(readings, [], [], now, 1.0)
    
    assert "patient_id" in df.columns
    assert "glucose_mgdl" in df.columns
    assert "heart_rate" in df.columns
    assert "steps" in df.columns
    assert "sleep_state" in df.columns
    assert "meal_carbs_g" in df.columns
    assert "activity_intensity" in df.columns
    
    # Ensure all numeric columns are strictly float64 with NaN for missing values
    numeric_cols = ["glucose_mgdl", "heart_rate", "steps", "meal_carbs_g", "activity_intensity"]
    for col in numeric_cols:
        assert df[col].dtype == np.float64, f"Column {col} has dtype {df[col].dtype}, expected float64"
    
    # Alignment adjusted
    assert any("snapped to" in a for a in adj)
    assert df[df["timestamp"] == pd.to_datetime("2024-01-01 12:00:00")]["glucose_mgdl"].iloc[0] == 100.0

def test_indicative_fuzz():
    from src.utils.config import load_config
    try:
        from src.twin.loader import TwinRegistry
    except ImportError:
        pytest.skip("Models not available")
        
    config = load_config()
    manifest_path = Path("models/FROZEN.json")
    if not manifest_path.exists():
        pytest.skip("Frozen models not present in this checkout")
        
    registry = TwinRegistry(config)
    now = datetime(2024, 1, 1, 12, 0)
    
    import random
    valid_count = 0
    invalid_count = 0
    
    for _ in range(300):
        if random.random() < 0.5:
            prof = {"age": random.randint(18, 90), "bmi": random.uniform(15, 60)}
        else:
            prof = {"age": 5, "bmi": 200}
            
        p, err_p = validate_profile(prof)
        
        if random.random() < 0.5:
            readings = [{"timestamp": now, "glucose_mgdl": random.uniform(40, 500)}]
        else:
            readings = []
            
        if len(err_p) == 0 and len(readings) > 0:
            df, _ = build_frame(readings, [], [], now, 24.0)
            res = run_indicative_path(df, p, config, registry.pipeline, registry.calibrator, registry.forecast_artifacts, registry.thresholds, explainer=None)
            assert res is not None
            assert res["risk"].probability_calibrated >= 0
            assert res["risk"].probability_calibrated <= 1
            valid_count += 1
        else:
            invalid_count += 1
            
    assert valid_count + invalid_count == 300

def test_privacy_static_scan():
    for p in ["src/app_lib/user_input.py", "app/pages/user_data_entry.py"]:
        path = Path(p)
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ["cache_data", "cache_resource"]:
                    pytest.fail(f"Found cache decorator in {p}")
        assert "patient_sim_params" not in content
        assert "baseline_insulin_sensitivity" not in content
        assert "archetype" not in content

def test_parity_twin_engine():
    from src.app_lib.data_access import get_patient_wearable, get_demo_patients, get_patients_df
    from src.utils.config import load_config
    try:
        from src.twin.loader import TwinRegistry
    except ImportError:
        pytest.skip("Models not available")
        
    config = load_config()
    manifest_path = Path("models/FROZEN.json")
    if not manifest_path.exists():
        pytest.skip("Frozen models not present in this checkout")
        
    registry = TwinRegistry(config)
    pids = get_demo_patients()
    if not pids or len(pids) < 3:
        pytest.skip("At least 3 demo patients required for parity test")
        
    prof_df = get_patients_df()
    features_list = list(registry.pipeline.feature_names_in_)
    
    from src.twin.engine import DiaTwin
    from src.twin.state import PatientProfile
    
    total_moments = 0
    gap_moments = 0
    overall_max_feat_diff = 0.0
    worst_feat_col = ""
    overall_max_prob_diff = 0.0
    overall_max_med_diff = 0.0
    overall_max_lower_diff = 0.0
    overall_max_upper_diff = 0.0
    
    for pid in pids[:3]:
        prof_dict = prof_df[prof_df["patient_id"] == pid].iloc[0].to_dict()
        prof = PatientProfile.from_dict(prof_dict)
        
        timeline = get_patient_wearable(pid).copy()
        timeline["timestamp"] = pd.to_datetime(timeline["timestamp"])
        
        twin = DiaTwin(
            prof, registry.pipeline, registry.calibrator, registry.thresholds,
            config, explainer=None, forecast_artifacts=registry.forecast_artifacts,
            whatif_artifacts=registry.whatif_artifacts
        )
        
        # Preload historical buffer
        buf = []
        for i in range(288):
            row = timeline.iloc[i]
            sample = {k: (float(v) if pd.notna(v) and k not in ["timestamp", "sleep_state", "patient_id"] else v) for k, v in row.to_dict().items()}
            sample["timestamp"] = row["timestamp"]
            buf.append(sample)
            twin._update_cumulative_state(sample)
        twin.buffer = buf
        twin.last_timestamp = timeline.iloc[287]["timestamp"]
        
        # Evaluate 20 moments for this demo patient
        for i in range(288, 308):
            row = timeline.iloc[i]
            sample = {k: (float(v) if pd.notna(v) and k not in ["timestamp", "sleep_state", "patient_id"] else v) for k, v in row.to_dict().items()}
            sample["timestamp"] = row["timestamp"].isoformat()
            
            twin_state = twin.ingest(sample)
            total_moments += 1
            
            buf_df = pd.DataFrame(twin.buffer)
            # Ensure float64 numeric columns
            numeric_cols = ["glucose_mgdl", "heart_rate", "steps", "meal_carbs_g", "activity_intensity"]
            for col in numeric_cols:
                buf_df[col] = pd.to_numeric(buf_df[col], errors="coerce").astype("float64")
                
            if buf_df["glucose_mgdl"].isna().any():
                gap_moments += 1
                
            ind_res = run_indicative_path(
                buf_df, prof_dict, config, registry.pipeline, registry.calibrator,
                registry.forecast_artifacts, registry.thresholds, explainer=None
            )
            
            twin_feat = twin._last_feature_row
            ind_feat = pd.DataFrame([ind_res["last_feat"]])
            
            for col in features_list:
                v1 = float(twin_feat[col].iloc[0])
                v2 = float(ind_feat[col].iloc[0])
                if pd.isna(v1) and pd.isna(v2):
                    d = 0.0
                elif pd.isna(v1) or pd.isna(v2):
                    d = 999.0
                else:
                    d = abs(v1 - v2)
                if d > overall_max_feat_diff:
                    overall_max_feat_diff = d
                    worst_feat_col = col
                    
            p1 = twin_state.risk.probability_calibrated if twin_state.risk else 0.0
            p2 = ind_res["risk"].probability_calibrated if ind_res["risk"] else 0.0
            d_prob = abs(p1 - p2)
            if d_prob > overall_max_prob_diff:
                overall_max_prob_diff = d_prob
                
            if twin_state.forecast and ind_res["forecast"]:
                m1 = twin_state.forecast.trajectory_5min["median"]
                m2 = ind_res["forecast"].trajectory_5min["median"]
                d_med = max(abs(a - b) for a, b in zip(m1, m2))
                if d_med > overall_max_med_diff:
                    overall_max_med_diff = d_med
                    
                l1 = twin_state.forecast.trajectory_5min["lower"]
                l2 = ind_res["forecast"].trajectory_5min["lower"]
                d_lower = max(abs(a - b) for a, b in zip(l1, l2))
                if d_lower > overall_max_lower_diff:
                    overall_max_lower_diff = d_lower
                    
                u1 = twin_state.forecast.trajectory_5min["upper"]
                u2 = ind_res["forecast"].trajectory_5min["upper"]
                d_upper = max(abs(a - b) for a, b in zip(u1, u2))
                if d_upper > overall_max_upper_diff:
                    overall_max_upper_diff = d_upper
                    
    print(f"\nParity summary: {total_moments} moments ({gap_moments} with gaps)")
    print(f"Max feature difference: {overall_max_feat_diff:.2e} (worst column: '{worst_feat_col}')")
    print(f"Max probability difference: {overall_max_prob_diff:.2e}")
    print(f"Max forecast median difference: {overall_max_med_diff:.2e}")
    print(f"Max conformal lower difference: {overall_max_lower_diff:.2e}")
    print(f"Max conformal upper difference: {overall_max_upper_diff:.2e}")
    
    assert total_moments >= 60, f"Expected at least 60 moments, got {total_moments}"
    assert gap_moments >= 6, f"Expected at least 6 moments with glucose gaps, got {gap_moments}"
    assert overall_max_feat_diff <= 1e-6, f"Feature parity exceeded 1e-6: {overall_max_feat_diff} on {worst_feat_col}"
    assert overall_max_prob_diff <= 1e-5, f"Probability parity exceeded 1e-5: {overall_max_prob_diff}"
    assert overall_max_med_diff <= 1e-5, f"Forecast median parity exceeded 1e-5: {overall_max_med_diff}"
    assert overall_max_lower_diff <= 1e-5, f"Conformal lower edge parity exceeded 1e-5: {overall_max_lower_diff}"
    assert overall_max_upper_diff <= 1e-5, f"Conformal upper edge parity exceeded 1e-5: {overall_max_upper_diff}"

def test_missing_reading_middle_history():
    from src.utils.config import load_config
    try:
        from src.twin.loader import TwinRegistry
    except ImportError:
        pytest.skip("Models not available")
        
    config = load_config()
    manifest_path = Path("models/FROZEN.json")
    if not manifest_path.exists():
        pytest.skip("Frozen models not present in this checkout")
        
    registry = TwinRegistry(config)
    now = datetime(2024, 1, 1, 12, 0)
    
    readings = [
        {"timestamp": now - timedelta(minutes=40), "glucose_mgdl": 140.0},
        # Gap at -35, -30, -25, -20
        {"timestamp": now - timedelta(minutes=5), "glucose_mgdl": 150.0},
    ]
    df, _ = build_frame(readings, [], [], now, 1.0)
    
    # Check that missing slots exist and have NaN
    assert df["glucose_mgdl"].isna().sum() > 0
    # Check numeric types
    for col in ["glucose_mgdl", "heart_rate", "steps", "meal_carbs_g", "activity_intensity"]:
        assert df[col].dtype == np.float64
        
    prof = {"age": 50, "bmi": 28.0, "hba1c": 7.0}
    res = run_indicative_path(df, prof, config, registry.pipeline, registry.calibrator, registry.forecast_artifacts, registry.thresholds)
    assert res is not None
    assert 0.0 <= res["risk"].probability_calibrated <= 1.0

def test_all_readings_missing():
    now = datetime(2024, 1, 1, 12, 0)
    valid_gluc, err_g = validate_glucose([], now)
    assert len(valid_gluc) == 0
    assert "At least one glucose reading is required." in err_g

def test_only_readings_older_than_20_minutes():
    now = datetime(2024, 1, 1, 12, 0)
    u_config = {"data_sufficiency": {
        "full_tier": {"min_history_hours": 24.0},
        "partial_tier": {"in_last_minutes": 45, "min_readings": 3, "min_span_minutes": 30},
        "single_tier": {"max_age_minutes": 20}
    }}
    readings = [{"timestamp": now - timedelta(minutes=35), "glucose_mgdl": 120.0}]
    df, _ = build_frame(readings, [], [], now, 1.0)
    tier, _ = evaluate_tier(df, now, u_config["data_sufficiency"])
    assert tier == "invalid"

def test_one_reading_only_single_tier():
    now = datetime(2024, 1, 1, 12, 0)
    u_config = {"data_sufficiency": {
        "full_tier": {"min_history_hours": 24.0},
        "partial_tier": {"in_last_minutes": 45, "min_readings": 3, "min_span_minutes": 30},
        "single_tier": {"max_age_minutes": 20}
    }}
    readings = [{"timestamp": now - timedelta(minutes=5), "glucose_mgdl": 125.0}]
    df, _ = build_frame(readings, [], [], now, 1.0)
    tier, missing_groups = evaluate_tier(df, now, u_config["data_sufficiency"])
    assert tier == "single"
    assert "24 hour history" in missing_groups

def test_provided_summary_text_parity():
    valid_gluc = [{"timestamp": datetime.now(), "glucose_mgdl": 110.0}]
    valid_meal = [{"timestamp": datetime.now(), "carbs": 30.0}]
    valid_ex = []
    missing_groups = ["24 hour history", "heart rate", "steps", "sleep"]
    
    summary = get_provided_summary(valid_gluc, valid_meal, valid_ex, missing_groups)
    assert summary["provided"] == "What was provided: Profile, 1 glucose reading(s), 1 meal(s), 0 exercise(s)."
    assert "What was NOT provided: 24 hour history, heart rate, steps, sleep." in summary["not_provided"]
    assert "Fixed placeholders are used for heart rate (70.0 bpm), steps (0.0), and sleep state (unknown)." in summary["not_provided"]
    assert "Features requiring history (personal 24-hour baseline and long lags) use training medians." in summary["not_provided"]
    assert "Synthetic mean glucose" in summary["cohort_comparison"]

def test_drivers_sorting_and_length():
    from src.utils.config import load_config
    try:
        from src.twin.loader import TwinRegistry
    except ImportError:
        pytest.skip("Models not available")
        
    config = load_config()
    manifest_path = Path("models/FROZEN.json")
    if not manifest_path.exists():
        pytest.skip("Frozen models not present in this checkout")
        
    registry = TwinRegistry(config)
    now = datetime(2024, 1, 1, 12, 0)
    
    # High risk profile to ensure drivers are triggered
    prof = {"age": 75, "bmi": 42.0, "hba1c": 12.0, "sex": "Male", "on_insulin": "Yes"}
    readings = [{"timestamp": now, "glucose_mgdl": 350.0}]
    df, _ = build_frame(readings, [], [], now, 24.0)
    
    res = run_indicative_path(df, prof, config, registry.pipeline, registry.calibrator, registry.forecast_artifacts, registry.thresholds, registry.explainer)
    if res["risk"].band in ["Medium", "High"] and registry.explainer is not None:
        drivers = res["risk"].drivers
        assert len(drivers) == 3, f"Expected exactly 3 drivers, got {len(drivers)}"
        assert abs(drivers[0]["shap_value"]) >= abs(drivers[1]["shap_value"]) >= abs(drivers[2]["shap_value"]), "Drivers not sorted descending by absolute SHAP value"

def test_default_schedule_produces_expected_sleep_features():
    from src.features.engineering import build_features_for_patient
    from src.utils.config import load_config
    config = load_config()
    
    now_dt = datetime(2024, 1, 2, 14, 0)
    readings = [{"timestamp": now_dt, "glucose_mgdl": 120.0}]
    df_day, _ = build_frame(readings, [], [], now_dt, 24.0)
    
    profile = pd.Series({
        "patient_id": "user_1", "age": 50, "sex": "F", "bmi": 26.0,
        "hba1c": 6.5, "diabetes_duration_years": 5.0, "on_insulin": 0,
        "on_metformin": 1, "hypertension": 0
    })
    
    feat_day = build_features_for_patient(df_day, profile, config)
    last_feat_day = feat_day.iloc[-1]
    
    assert df_day["sleep_state"].iloc[-1] == "awake"
    assert last_feat_day["sleep_is_asleep"] == 0
    assert last_feat_day["sleep_state_awake"] == 1
    assert last_feat_day["sleep_state_light"] == 0
    assert last_feat_day["sleep_min_since_wake"] > 0
    
    now_night = datetime(2024, 1, 2, 2, 0)
    df_night, _ = build_frame([{"timestamp": now_night, "glucose_mgdl": 110.0}], [], [], now_night, 24.0)
    feat_night = build_features_for_patient(df_night, profile, config)
    last_feat_night = feat_night.iloc[-1]
    
    assert df_night["sleep_state"].iloc[-1] == "light"
    assert last_feat_night["sleep_is_asleep"] == 1
    assert last_feat_night["sleep_state_light"] == 1
    assert last_feat_night["sleep_state_awake"] == 0
    assert last_feat_night["sleep_min_since_wake"] == 0.0

def test_page_text_equals_generated_text():
    valid_gluc = [{"timestamp": datetime(2024, 1, 1, 12, 0), "glucose_mgdl": 110.0}]
    valid_meal = [{"timestamp": datetime(2024, 1, 1, 11, 0), "carbs": 30.0}]
    valid_ex = []
    missing_groups = ["24 hour history", "heart rate", "steps", "sleep: assumed schedule (not measured)"]
    
    summary = get_provided_summary(valid_gluc, valid_meal, valid_ex, missing_groups)
    assert "sleep: assumed schedule (not measured)" in summary["not_provided"]
    assert "Sleep uses assumed schedule 23:00 to 07:00" in summary["not_provided"]
    
    stmt = get_sensitivity_statement("indicative")
    assert "on synthetic validation patients the estimate without sensors differed from the full estimate by" in stmt
    assert "in probability and kept the same band in" in stmt
    assert "percent of moments" in stmt

def test_confidence_label_never_high_for_non_full_tiers():
    u_config = {"partial_tier": {"allow_medium_confidence": True}}
    for tier in ["single", "partial", "invalid", "none", "unknown"]:
        label = get_confidence_label(tier, u_config)
        assert label != "High", f"Tier {tier} had confidence {label}, expected not High"
        assert label in ["Low", "Medium"]
        
    assert get_confidence_label("full", u_config) == "High"

