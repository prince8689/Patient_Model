import os
import sys
import tempfile
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

def hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

def test_data_generation_determinism():
    print("--- Data Generation Determinism ---")
    from src.utils.config import load_config
    root = Path(__file__).resolve().parent.parent.parent
    config = load_config(root / "configs/config.yaml")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Override paths
        config["paths"]["data_raw"] = str(temp_path)
        
        # Run seed 42
        config["random_seed"] = 42
        from src.data_gen.patients import generate_patients
        from src.data_gen.wearable import generate_wearable
        
        p1, s1 = generate_patients(10, seed=42)
        w1 = generate_wearable(p1, s1, config)
        
        # Run seed 42 again
        p2, s2 = generate_patients(10, seed=42)
        w2 = generate_wearable(p2, s2, config)
        
        # Run seed 99
        config["random_seed"] = 99
        p3, s3 = generate_patients(10, seed=99)
        w3 = generate_wearable(p3, s3, config)
        
        assert p1.equals(p2), "Patients generation is NOT deterministic for same seed"
        assert not p1.equals(p3), "Patients generation did NOT change for different seed"
        
        pd.testing.assert_frame_equal(w1, w2, obj="Wearable df (seed 42 run 1 vs 2)")
        assert not w1.equals(w3), "Wearable generation did NOT change for different seed"
        print("Data Generation Determinism: PASS")

def test_feature_determinism():
    print("--- Feature Building Determinism ---")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        root = Path(__file__).resolve().parent.parent.parent
        from src.utils.config import load_config
        config = load_config(root / "configs/config.yaml")
        config["paths"]["data_processed"] = str(temp_path)
        
        raw_patients = pd.read_csv(root / "data" / "raw" / "patients.csv").head(2)
        raw_wearable = pd.read_csv(root / "data" / "raw" / "wearable.csv")
        raw_wearable = raw_wearable[raw_wearable["patient_id"].isin(raw_patients["patient_id"])]
        
        from src.features.engineering import build_features
        
        features1 = build_features(raw_wearable, raw_patients, config)
        features1.to_parquet(temp_path / "features1.parquet", index=False)
        h1 = hash_file(temp_path / "features1.parquet")
        
        features2 = build_features(raw_wearable, raw_patients, config)
        features2.to_parquet(temp_path / "features2.parquet", index=False)
        h2 = hash_file(temp_path / "features2.parquet")
        
        assert h1 == h2, "Feature building is NOT deterministic"
        print("Feature Building Determinism: PASS")

def test_model_determinism():
    print("--- Model Determinism ---")
    root = Path(__file__).resolve().parent.parent.parent
    from src.utils.config import load_config
    config = load_config(root / "configs/config.yaml")
    
    import joblib
    import xgboost as xgb
    model = joblib.load(root / "models" / "xgb_v1.joblib")
    
    df = pd.read_parquet(root / "data" / "processed" / "features.parquet")
    X = df.drop(columns=["patient_id", "timestamp", "split", "valid", "spike_next_2h"])
    X = X.head(100)
    
    model.set_params(n_jobs=1)
    p1 = model.predict_proba(X)[:, 1]
    
    model.set_params(n_jobs=4)
    p2 = model.predict_proba(X)[:, 1]
    
    diff = np.max(np.abs(p1 - p2))
    print(f"Max diff between n_jobs=1 and n_jobs=4: {diff}")
    assert diff < 1e-9, "Model prediction is NOT deterministic across n_jobs"
    print("Model Determinism: PASS")

def test_twin_replay_determinism():
    print("--- Twin Streaming Replay Determinism ---")
    root = Path(__file__).resolve().parent.parent.parent
    from src.utils.config import load_config
    config = load_config(root / "configs/config.yaml")
    
    from src.twin.loader import TwinRegistry
    registry = TwinRegistry(config)
    
    # Run 1
    t1 = registry.register("P001")
    from src.twin.replay import StreamReplayer
    r1 = StreamReplayer(str(root / "data" / "raw" / "wearable.csv"), "P001", end_time="2026-01-04T00:00:00")
    for sample in r1.stream():
        t1.ingest(sample)
    state1 = t1.get_state()
    
    # Run 2
    t2 = registry.register("P001") # this will return the same twin instance actually?
    # Registry returns the same instance! We need a fresh one.
    registry2 = TwinRegistry(config)
    t2 = registry2.register("P001")
    r2 = StreamReplayer(str(root / "data" / "raw" / "wearable.csv"), "P001", end_time="2026-01-04T00:00:00")
    for sample in r2.stream():
        t2.ingest(sample)
    state2 = t2.get_state()
    
    # compare dicts
    assert state1.to_dict() == state2.to_dict(), "Replay is NOT deterministic"
    
    # Snapshot / restore
    snap = t2.snapshot()
    registry3 = TwinRegistry(config)
    t3 = registry3.register("P001")
    t3.restore(snap)
    state3 = t3.get_state()
    
    # Remove things that aren't strictly restorable (if any)
    d2 = state2.to_dict()
    d3 = state3.to_dict()
    
    # The drivers might be slightly different if SHAP randomness exists, but tree explainer is deterministic
    assert d2 == d3, "Snapshot/Restore is NOT deterministic"
    print("Twin Streaming Replay Determinism: PASS")

if __name__ == "__main__":
    test_data_generation_determinism()
    test_feature_determinism()
    test_model_determinism()
    test_twin_replay_determinism()
