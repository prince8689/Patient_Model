import sys
import os
import json
import joblib
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.forecast.conformal import ConformalCalibrator
from scripts.evaluate_forecast_val import clarke_error_grid

def get_file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def check_guards(config):
    if os.environ.get("ALLOW_TEST") != "1":
        raise ValueError("ALLOW_TEST=1 is required to run test evaluation.")
        
    manifest_path = Path(config["forecast"]["manifest_path"])
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing {manifest_path}. Freeze forecast first.")
        
    test_done_path = Path(config["forecast"]["test_done_path"])
    if test_done_path.exists() and "--force" not in sys.argv:
        raise ValueError(f"{test_done_path} exists. Test evaluation already ran.")
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    models_dir = Path("models")
    files_to_hash = [
        models_dir / "forecaster_v1.joblib",
        models_dir / "forecaster_v1_meta.json",
        models_dir / "forecast_conformal_v1.json",
        Path("configs") / "config.yaml"
    ]
    
    for f in files_to_hash:
        expected = manifest["files"][f.name]
        actual = get_file_hash(f)
        if expected != actual:
            raise ValueError(f"Hash mismatch for {f.name}: expected {expected}, got {actual}")
            
def main():
    config = load_config()
    check_guards(config)
    
    data_dir = Path(config["paths"]["data_processed"])
    models_dir = Path(config["forecast"]["models_dir"])
    fig_dir = Path(config["paths"]["reports"]) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    models = joblib.load(models_dir / "forecaster_v1.joblib")
    with open(models_dir / "forecaster_v1_meta.json", "r") as f:
        meta = json.load(f)
    with open(models_dir / "forecast_conformal_v1.json", "r") as f:
        conformal_meta = json.load(f)
        
    df = pd.read_parquet(data_dir / "features.parquet")
    targets_df = pd.read_parquet(data_dir / "forecast_targets.parquet")
    
    df = df.merge(targets_df, on=["patient_id", "timestamp"])
    test_df = df[df["split"] == "test"].copy()
    
    X_test = test_df[meta["features"]]
    horizons = meta["horizons"]
    
    # Predict
    preds_persist = models["persist"].predict_quantiles(X_test)
    preds_linear = models["linear"].predict_quantiles(X_test)
    preds_ridge = models["ridge"].predict_quantiles(X_test)
    preds_xgb = models["xgb"].predict_quantiles(X_test)
    
    # Calibrate
    calibrator = ConformalCalibrator(horizons, meta["quantiles"], config["forecast"]["nominal_interval_coverage"])
    calibrator.q_hat = {int(k): v for k, v in conformal_meta["q_hat"].items()}
    preds_xgb_cal = calibrator.apply(preds_xgb)
    
    metrics = []
    for i, h in enumerate(horizons):
        y = test_df[f"target_delta_{h}m"].values
        mask = ~np.isnan(y)
        y_valid = y[mask]
        
        pred_med = preds_xgb[mask, i, 1]
        pred_low = preds_xgb_cal[mask, i, 0]
        pred_high = preds_xgb_cal[mask, i, 2]
        
        mae = np.mean(np.abs(y_valid - pred_med))
        rmse = np.sqrt(np.mean((y_valid - pred_med)**2))
        cov_cal = np.mean((y_valid >= pred_low) & (y_valid <= pred_high))
        
        metrics.append({
            "horizon": h,
            "mae": mae,
            "rmse": rmse,
            "coverage_cal": cov_cal
        })
        
    mdf = pd.DataFrame(metrics)
    print("\nTEST Metrics:")
    print(mdf.to_string())
    
    # Write done file
    with open(config["forecast"]["test_done_path"], "w") as f:
        json.dump({"status": "done"}, f)
        
    print("Done test evaluation.")

if __name__ == "__main__":
    main()
