import numpy as np
import pandas as pd
import pytest

from src.data_gen.labels import make_labels
from src.data_gen.splits import assert_no_patient_overlap, make_patient_splits


def test_make_labels():
    config = {
        "prediction_horizon_minutes": 10,
        "sampling_interval_minutes": 5, # 2 steps
        "spike_threshold_mgdl": 50,
        "label_min_future_coverage": 0.5
    }
    
    df = pd.DataFrame({
        "patient_id": ["P1"]*6 + ["P2"]*3,
        "timestamp": pd.date_range("2026-01-01", periods=9, freq="5min"),
        "glucose_mgdl": [100, 110, 150, np.nan, 120, 100,  100, 160, 100]
    })
    
    labels = make_labels(df, config)
    
    # P1:
    # 0: 100. future: [110, 150]. max=150. spike=1. valid=1
    # 1: 110. future: [150, nan]. max=150. count=1/2 >= 0.5 -> valid=1. spike=0
    # 2: 150. future: [nan, 120]. max=120. count=1/2 -> valid=1. spike=0
    # 3: nan. valid=0
    # 4: 120. valid=0 (excluded, only 1 step left)
    # 5: 100. valid=0 (excluded, 0 steps left)
    # P2:
    # 6: 100. future: [160, 100]. max=160. spike=1. valid=1
    # 7: 160. valid=0 (excluded)
    # 8: 100. valid=0 (excluded)
    
    assert labels.loc[0, "valid"] == 1 and labels.loc[0, "spike_next_2h"] == 1
    assert labels.loc[1, "valid"] == 1 and labels.loc[1, "spike_next_2h"] == 0
    assert labels.loc[2, "valid"] == 1 and labels.loc[2, "spike_next_2h"] == 0
    assert labels.loc[3, "valid"] == 0 and pd.isna(labels.loc[3, "spike_next_2h"])
    assert labels.loc[4, "valid"] == 0
    
    assert labels.loc[6, "valid"] == 1 and labels.loc[6, "spike_next_2h"] == 1

def test_make_splits():
    config = {"random_seed": 42, "split": {"train": 0.7, "val": 0.15, "test": 0.15}}
    pdf = pd.DataFrame({
        "patient_id": [f"P{i}" for i in range(40)],
        "hba1c": np.linspace(5.0, 12.0, 40)
    })
    
    splits = make_patient_splits(pdf, config)
    assert len(splits) == 40
    assert_no_patient_overlap(splits)
    
    counts = splits["split"].value_counts()
    assert counts["train"] == 28
    assert counts["val"] == 6
    assert counts["test"] == 6
    
    # Stratification check (each split should have patients from different ranges)
    merged = splits.merge(pdf, on="patient_id")
    for s in ["train", "val", "test"]:
        hba1c_vals = merged[merged["split"] == s]["hba1c"]
        assert hba1c_vals.max() > 9.0
        assert hba1c_vals.min() < 7.0

def test_split_overlap_raises():
    bad_splits = pd.DataFrame({"patient_id": ["P1", "P2", "P1"], "split": ["train", "val", "test"]})
    with pytest.raises(ValueError, match="overlap"):
        assert_no_patient_overlap(bad_splits)
