import sys
import json
import joblib
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import precision_recall_curve, f1_score

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.features.registry import FEATURE_REGISTRY
from src.models.calibration import apply_calibration

def get_threshold_for_precision(y_true, y_prob, target_precision):
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_prob)
    for p, t in zip(precisions, thresholds):
        if p >= target_precision:
            return t
    return None # Target unreachable

def main():
    config = load_config()
    feat_path = Path(config["paths"]["data_processed"]) / "features.parquet"
    models_path = Path(config["paths"]["models"])
    
    print("Loading features and models...")
    df = pd.read_parquet(feat_path)
    val_mask = (df["split"] == "val") & (df["valid"] == 1)
    df_val = df[val_mask].copy()
    
    with open(models_path / "xgb_v1_meta.json", "r") as f:
        meta = json.load(f)
    features = meta["features"]
    
    model = joblib.load(models_path / "xgb_v1.joblib")
    calibrator = joblib.load(models_path / "calibrator_v1.joblib")
    
    print("Predicting on VAL...")
    X_val = df_val[features]
    y_val = df_val["spike_next_2h"]
    prob_raw = model.predict_proba(X_val)[:, 1]
    prob_calib = apply_calibration(prob_raw, calibrator)
    
    policy = config["evaluation"]["risk_band_policy"]
    p_med_target = policy["low_max_percentile_precision"]
    p_high_target = policy["high_min_precision"]
    
    t_med = get_threshold_for_precision(y_val, prob_calib, p_med_target)
    t_high = get_threshold_for_precision(y_val, prob_calib, p_high_target)
    
    fallback_used = False
    if t_med is None:
        # fallback to best F1
        precisions, recalls, thresholds = precision_recall_curve(y_val, prob_calib)
        f1s = 2 * (precisions * recalls) / (precisions + recalls + 1e-9)
        t_med = thresholds[np.argmax(f1s)]
        fallback_used = True
        print("WARNING: t_med target precision unreachable. Falling back to best F1.")
        
    if t_high is None:
        t_high = np.percentile(prob_calib, 90)
        fallback_used = True
        print("WARNING: t_high target precision unreachable. Falling back to 90th percentile.")
        
    # Bootstrap uncertainty
    n_boot = config["evaluation"]["n_bootstrap"]
    patients = df_val["patient_id"].unique()
    t_med_boots = []
    t_high_boots = []
    
    np.random.seed(42)
    for _ in range(n_boot):
        boot_pats = np.random.choice(patients, size=len(patients), replace=True)
        boot_df = pd.concat([df_val[df_val["patient_id"] == p] for p in boot_pats])
        y_b = boot_df["spike_next_2h"]
        p_b = boot_df["prob_calib"] if "prob_calib" in boot_df.columns else apply_calibration(model.predict_proba(boot_df[features])[:, 1], calibrator)
        
        t_m = get_threshold_for_precision(y_b, p_b, p_med_target)
        if t_m is None: t_m = t_med
        t_med_boots.append(t_m)
        
        t_h = get_threshold_for_precision(y_b, p_b, p_high_target)
        if t_h is None: t_h = t_high
        t_high_boots.append(t_h)
        
    t_med_ci = np.percentile(t_med_boots, [5, 95])
    t_high_ci = np.percentile(t_high_boots, [5, 95])
    
    print(f"Threshold Medium: {t_med:.4f} (90% CI: {t_med_ci[0]:.4f} - {t_med_ci[1]:.4f})")
    print(f"Threshold High: {t_high:.4f} (90% CI: {t_high_ci[0]:.4f} - {t_high_ci[1]:.4f})")
    
    out = {
        "thresholds": {
            "t_medium": float(t_med),
            "t_high": float(t_high)
        },
        "bands": {
            "Low": f"< {t_med:.4f}",
            "Medium": f"[{t_med:.4f}, {t_high:.4f})",
            "High": f">= {t_high:.4f}"
        },
        "alert_threshold": float(t_med),
        "method": "precision-targets" if not fallback_used else "fallback",
        "calibrated": True
    }
    
    with open(models_path / "thresholds_v1.json", "w") as f:
        json.dump(out, f, indent=2)
        
    print("Saved models/thresholds_v1.json")

if __name__ == "__main__":
    main()
