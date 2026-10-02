import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.model_selection import GroupKFold

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config


def expected_calibration_error(y_true, y_prob, n_bins=10):
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy='quantile')
    
    # ECE is weighted average of absolute differences
    bin_counts = np.histogram(y_prob, bins=n_bins)[0]
    # Simple approx ECE
    ece = np.mean(np.abs(prob_true - prob_pred))
    return ece

def main():
    config = load_config()
    feat_path = Path(config["paths"]["data_processed"]) / "features.parquet"
    models_path = Path(config["paths"]["models"])
    reports_path = Path(config["paths"]["reports"])
    fig_dir = reports_path / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading features...")
    df = pd.read_parquet(feat_path)
    
    with open(models_path / "xgb_v1_meta.json", "r") as f:
        meta = json.load(f)
    
    features = meta["features"]
    hyperparams = meta["hyperparameters"]
    
    train_mask = (df["split"] == "train") & (df["valid"] == 1)
    val_mask = (df["split"] == "val") & (df["valid"] == 1)
    
    df_train = df[train_mask].copy().reset_index(drop=True)
    df_val = df[val_mask].copy().reset_index(drop=True)
    
    X_train = df_train[features]
    y_train = df_train["spike_next_2h"]
    groups_train = df_train["patient_id"]
    
    X_val = df_val[features]
    y_val = df_val["spike_next_2h"]
    
    # OOF probabilities
    gkf = GroupKFold(n_splits=5)
    oof_preds = np.zeros(len(df_train))
    
    print("Generating OOF predictions on Train...")
    for fold, (trn_idx, val_idx) in enumerate(gkf.split(X_train, y_train, groups=groups_train)):
        print(f"Fold {fold+1}...")
        model = xgb.XGBClassifier(**hyperparams)
        model.fit(X_train.iloc[trn_idx], y_train.iloc[trn_idx])
        oof_preds[val_idx] = model.predict_proba(X_train.iloc[val_idx])[:, 1]
        
    df_train["prob_raw"] = oof_preds
    df_train[["patient_id", "timestamp", "spike_next_2h", "prob_raw"]].to_parquet(reports_path / "oof_train_day7.parquet")
    
    # Val raw probabilities using the already trained full model
    final_model = joblib.load(models_path / "xgb_v1.joblib")
    val_raw = final_model.predict_proba(X_val)[:, 1]
    
    # Fit calibrators on OOF Train
    iso = IsotonicRegression(out_of_bounds='clip')
    iso.fit(oof_preds, y_train)
    
    sig = LogisticRegression()
    sig.fit(oof_preds.reshape(-1, 1), y_train)
    
    # Evaluate on Val
    val_iso = iso.transform(val_raw)
    val_sig = sig.predict_proba(val_raw.reshape(-1, 1))[:, 1]
    
    metrics = []
    for name, p_val in [("raw", val_raw), ("isotonic", val_iso), ("sigmoid", val_sig)]:
        brier = brier_score_loss(y_val, p_val)
        ll = log_loss(y_val, p_val)
        ece = expected_calibration_error(y_val, p_val, 10)
        metrics.append({"method": name, "brier": brier, "log_loss": ll, "ece": ece})
        print(f"{name.upper()}: Brier={brier:.4f}, LogLoss={ll:.4f}, ECE={ece:.4f}")
        
    metrics_df = pd.DataFrame(metrics).set_index("method")
    
    # Choose best calibrator (prefer sigmoid if close)
    iso_brier = metrics_df.loc["isotonic", "brier"]
    sig_brier = metrics_df.loc["sigmoid", "brier"]
    
    if sig_brier <= iso_brier + 0.001:
        best_name = "sigmoid"
        best_calibrator = sig
    else:
        best_name = "isotonic"
        best_calibrator = iso
        
    print(f"Chosen Calibrator: {best_name}")
    joblib.dump(best_calibrator, models_path / "calibrator_v1.joblib")
    
    # Plot Reliability Curve
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1)
    fop_raw, mpv_raw = calibration_curve(y_val, val_raw, n_bins=10, strategy='quantile')
    plt.plot(mpv_raw, fop_raw, marker='o', label="Raw")
    
    p_val_best = val_sig if best_name == "sigmoid" else val_iso
    fop_calib, mpv_calib = calibration_curve(y_val, p_val_best, n_bins=10, strategy='quantile')
    plt.plot(mpv_calib, fop_calib, marker='s', label=f"Calibrated ({best_name})")
    plt.plot([0, 1], [0, 1], 'k:', label="Perfect")
    plt.title("Reliability Diagram (VAL)")
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.hist(val_raw, bins=20, alpha=0.5, label="Raw")
    plt.hist(p_val_best, bins=20, alpha=0.5, label="Calibrated")
    plt.title("Prediction Histograms (VAL)")
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(fig_dir / "day7_calibration_val_before_after.png", dpi=150)
    
if __name__ == "__main__":
    main()
