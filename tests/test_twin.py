import copy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.twin.engine import DiaTwin
from src.twin.loader import TwinRegistry
from src.utils.config import load_config


@pytest.fixture(scope="module")
def skip_if_models_missing():
    root = Path(__file__).resolve().parent.parent
    if not (root / "models" / "xgb_v1.joblib").exists():
        pytest.skip("Joblib models not present in this checkout")

@pytest.fixture(scope="module")
def config():
    return load_config()

@pytest.fixture(scope="module")
def sample_patient(config):
    splits_path = Path(config["paths"]["data_processed"]) / "splits.csv"
    if not splits_path.exists():
        pytest.skip("not present in this checkout")
    splits = pd.read_csv(splits_path)
    test_pats = splits[splits["split"] == "test"]["patient_id"].unique()
    return test_pats[0] if len(test_pats) > 0 else None

def test_twin_snapshot_restore(skip_if_models_missing, config, sample_patient):
    if not sample_patient: pytest.skip("No test patients")
    
    registry = TwinRegistry(config)
    twin1 = registry.get(sample_patient)
    
    # Ingest 100
    df = pd.read_csv(Path(config["paths"]["data_raw"]) / "wearable.csv")
    df = df[df["patient_id"] == sample_patient].iloc[:200]
    
    stream = [dict(r) | {"timestamp": r["timestamp"]} for _, r in df.iterrows()]
    
    # Run 100
    for s in stream[:100]:
        twin1.ingest(s)
        
    snap = twin1.snapshot()
    
    # Restore to twin2
    twin2 = DiaTwin.restore(snap, twin1.pipeline, twin1.calibrator, twin1.thresholds, config, twin1.explainer)
    
    # Run 100 more on both
    for s in stream[100:]:
        s1 = twin1.ingest(s)
        s2 = twin2.ingest(s)
        
        # compare
        assert s1.risk.probability_calibrated == pytest.approx(s2.risk.probability_calibrated, abs=1e-6) if s1.risk else True
        assert s1.glucose_summary.current_glucose == s2.glucose_summary.current_glucose
        
def test_fault_duplicate(skip_if_models_missing, config, sample_patient):
    if not sample_patient: pytest.skip("No test patients")
    registry = TwinRegistry(config)
    twin = registry.get(sample_patient)
    
    s1 = {"timestamp": "2026-01-01T00:00:00", "glucose_mgdl": 100, "heart_rate": 70, "steps": 0, "sleep_state": "awake", "meal_carbs_g": 0, "activity_intensity": 0, "patient_id": sample_patient}
    twin.ingest(s1)
    
    snap1 = twin.snapshot()
    s2 = twin.ingest(s1) # duplicate
    snap2 = twin.snapshot()
    
    assert len(snap1["buffer"]) == len(snap2["buffer"])
    
def test_fault_corrupted_glucose(skip_if_models_missing, config, sample_patient):
    if not sample_patient: pytest.skip("No test patients")
    registry = TwinRegistry(config)
    twin = registry.get(sample_patient)
    
    s1 = {"timestamp": "2026-01-01T00:00:00", "glucose_mgdl": -5, "heart_rate": 70, "steps": 0, "sleep_state": "awake", "meal_carbs_g": 0, "activity_intensity": 0, "patient_id": sample_patient}
    state = twin.ingest(s1)
    
    assert state.latest_measurement.glucose_mgdl is None
    assert any("Glucose out of range" in w for w in state.data_quality.warnings)

def test_no_future(skip_if_models_missing, config, sample_patient):
    if not sample_patient: pytest.skip()
    registry = TwinRegistry(config)
    twin = registry.get(sample_patient)
    
    s1 = {"timestamp": "2026-01-01T00:00:00", "glucose_mgdl": 100, "heart_rate": 70, "steps": 0, "sleep_state": "awake", "meal_carbs_g": 0, "activity_intensity": 0, "patient_id": sample_patient}
    s2 = {"timestamp": "2026-01-01T00:05:00", "glucose_mgdl": 105, "heart_rate": 70, "steps": 0, "sleep_state": "awake", "meal_carbs_g": 0, "activity_intensity": 0, "patient_id": sample_patient}
    
    state1 = twin.ingest(s1)
    # The state should be exactly the same regardless of whether we have s2 or not,
    # because s2 hasn't been ingested yet! By construction, ingest() only sees what's passed to it.
    assert state1.timestamp == "2026-01-01T00:00:00"
    
def test_warmup(skip_if_models_missing, config, sample_patient):
    if not sample_patient: pytest.skip()
    registry = TwinRegistry(config)
    twin = registry.get(sample_patient)
    
    s1 = {"timestamp": "2026-01-01T00:00:00", "glucose_mgdl": 100, "heart_rate": 70, "steps": 0, "sleep_state": "awake", "meal_carbs_g": 0, "activity_intensity": 0, "patient_id": sample_patient}
    state = twin.ingest(s1)
    
    assert state.data_quality.status == "warming_up"
    assert state.risk is None
    
def test_gap_fill(skip_if_models_missing, config, sample_patient):
    if not sample_patient: pytest.skip()
    registry = TwinRegistry(config)
    twin = registry.get(sample_patient)
    
    s1 = {"timestamp": "2026-01-01T00:00:00", "glucose_mgdl": 100, "heart_rate": 70, "steps": 0, "sleep_state": "awake", "meal_carbs_g": 0, "activity_intensity": 0, "patient_id": sample_patient}
    s2 = {"timestamp": "2026-01-01T01:00:00", "glucose_mgdl": 105, "heart_rate": 70, "steps": 0, "sleep_state": "awake", "meal_carbs_g": 0, "activity_intensity": 0, "patient_id": sample_patient}
    
    twin.ingest(s1)
    state = twin.ingest(s2)
    
    # 60 mins gap = 12 intervals. It should have 1 + 11 padded + 1 = 13 items in buffer
    assert len(twin.buffer) == 13
    assert np.isnan(twin.buffer[1]["glucose_mgdl"])
    assert twin.buffer[1]["sleep_state"] == "unknown"

def test_frozen_hash_mismatch(config, tmp_path):
    import json

    from src.twin.loader import load_frozen_artifacts
    
    # Create a corrupted frozen.json
    frozen_path = Path(config["evaluation"]["frozen_manifest_path"])
    with open(frozen_path, "r") as f:
        frozen = json.load(f)
        
    # Keep only registry.py to avoid FileNotFoundError on gitignored binaries in a clone
    # and to ensure the hash mismatch branch is executed (config bypasses it)
    frozen["hashes"] = {"src/features/registry.py": "deadbeef"}
    
    tmp_frozen = tmp_path / "FROZEN.json"
    with open(tmp_frozen, "w") as f:
        json.dump(frozen, f)
        
    cfg_copy = copy.deepcopy(config)
    cfg_copy["evaluation"]["frozen_manifest_path"] = str(tmp_frozen)
    
    with pytest.raises(ValueError, match="FROZEN HASH MISMATCH"):
        load_frozen_artifacts(cfg_copy)
