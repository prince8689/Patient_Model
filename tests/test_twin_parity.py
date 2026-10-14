from pathlib import Path

import pandas as pd
import pytest

from src.twin.loader import TwinRegistry
from src.twin.replay import StreamReplayer
from src.utils.config import load_config


@pytest.fixture(scope="module", autouse=True)
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
        pytest.skip("splits.csv not present in this checkout")
    splits = pd.read_csv(splits_path)
    test_pats = splits[splits["split"] == "test"]["patient_id"].unique()
    if len(test_pats) == 0:
        pytest.skip("Test patients not present in this checkout")
    return test_pats[0]

def test_twin_feature_parity(config, sample_patient):
    # Load batch features
    feat_path = Path(config["paths"]["data_processed"]) / "features.parquet"
    if not feat_path.exists():
        pytest.skip("Batch features not present in this checkout")
        
    df_feat = pd.read_parquet(feat_path)
    df_feat = df_feat[df_feat["patient_id"] == sample_patient].copy()
    df_feat["timestamp"] = pd.to_datetime(df_feat["timestamp"])
    df_feat = df_feat.set_index("timestamp")
    
    # Initialize twin
    registry = TwinRegistry(config)
    twin = registry.get(sample_patient)
    
    # Stream for a few days
    replayer = StreamReplayer(Path(config["paths"]["data_raw"]) / "wearable.csv", sample_patient)
    stream = list(replayer.stream())
    
    warmup_samples = int(config["twin"]["warmup_hours"] * 60 / config["sampling_interval_minutes"])
    test_samples = stream[:warmup_samples + 200]
    
    mismatches = {}
    
    for i, sample in enumerate(test_samples):
        state = twin.ingest(sample)
        ts = pd.to_datetime(state.timestamp)
        
        # Only check after warmup
        if i >= warmup_samples:
            if ts not in df_feat.index:
                continue
                
            batch_row = df_feat.loc[ts]
            twin_row = twin._last_feature_row.iloc[0]
            
            features = twin.pipeline.feature_names_in_
            
            for f in features:
                val_b = batch_row[f]
                val_t = twin_row[f]
                
                if pd.isna(val_b) and pd.isna(val_t):
                    continue
                if pd.isna(val_b) != pd.isna(val_t) or abs(val_b - val_t) > 1e-6:
                    if f not in mismatches:
                        mismatches[f] = []
                    mismatches[f].append((ts, val_b, val_t))
                    
    if mismatches:
        err_msg = "Feature parity failed for:\n"
        for f, errs in mismatches.items():
            err_msg += f"  {f} (n={len(errs)} mismatches, e.g. at {errs[0][0]}: batch={errs[0][1]}, twin={errs[0][2]})\n"
        pytest.fail(err_msg)

def test_twin_probability_parity(config, sample_patient):
    # Same concept, check probability_calibrated
    feat_path = Path(config["paths"]["data_processed"]) / "features.parquet"
    if not feat_path.exists():
        pytest.skip("Batch features not present in this checkout")
        
    df_feat = pd.read_parquet(feat_path)
    df_feat = df_feat[df_feat["patient_id"] == sample_patient].copy()
    df_feat["timestamp"] = pd.to_datetime(df_feat["timestamp"])
    df_feat = df_feat.set_index("timestamp")
    
    registry = TwinRegistry(config)
    twin = registry.get(sample_patient)
    
    replayer = StreamReplayer(Path(config["paths"]["data_raw"]) / "wearable.csv", sample_patient)
    stream = list(replayer.stream())
    
    warmup_samples = int(config["twin"]["warmup_hours"] * 60 / config["sampling_interval_minutes"])
    test_samples = stream[:warmup_samples + 200]
    
    # We need batch probabilities. Since stored test_predictions_day7.parquet exists, we can use that!
    pred_path = Path(config["paths"]["reports"]) / "test_predictions_day7.parquet"
    if not pred_path.exists():
        pytest.skip("Batch predictions not present in this checkout")
    df_pred = pd.read_parquet(pred_path)
    df_pred = df_pred[df_pred["patient_id"] == sample_patient].copy()
    df_pred["timestamp"] = pd.to_datetime(df_pred["timestamp"])
    df_pred = df_pred.set_index("timestamp")
    
    for i, sample in enumerate(test_samples):
        state = twin.ingest(sample)
        ts = pd.to_datetime(state.timestamp)
        
        if i >= warmup_samples:
            if ts not in df_pred.index:
                continue
            
            batch_p = df_pred.loc[ts, "prob_calib"]
            twin_p = state.risk.probability_calibrated
            
            assert abs(batch_p - twin_p) <= 1e-5, f"Probability mismatch at {ts}: batch={batch_p}, twin={twin_p}"
