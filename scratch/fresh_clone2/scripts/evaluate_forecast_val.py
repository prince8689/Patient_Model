import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.forecast.conformal import ConformalCalibrator
from src.utils.config import load_config


def pinball_loss(y_true, y_pred, q):
    err = y_true - y_pred
    return np.mean(np.maximum(q * err, (q - 1) * err))

def clarke_error_grid(ref, pred):
    # Simplified Clarke Error Grid
    # ref and pred are absolute glucose values
    ref = np.asarray(ref)
    pred = np.asarray(pred)
    
    zones = np.empty(len(ref), dtype=str)
    
    # Zone A: within 20% or within 15 mg/dl if ref <= 70
    abs_diff = np.abs(ref - pred)
    zone_a = (abs_diff <= 0.2 * ref) | ((ref <= 70) & (pred <= 70)) | ((ref <= 70) & (abs_diff <= 15))
    
    # Zone B: not A, but wouldn't lead to inappropriate treatment
    # We'll approximate: upper bound 1.2*ref or lower bound if high etc.
    # Simplified standard heuristic:
    zone_b = ~zone_a & (
        ((ref < 70) & (pred <= 70)) |
        ((ref >= 70) & (pred >= 70) & (abs_diff <= 0.4 * ref))
    )
    
    # Zone C: unnecessary treatment
    zone_c = ~zone_a & ~zone_b & (
        ((ref >= 130) & (pred <= 70)) |
        ((ref <= 70) & (pred >= 130))
    )
    
    # Zone D: failure to detect hypo or hyper
    zone_d = ~zone_a & ~zone_b & ~zone_c & (
        ((ref < 70) & (pred > 70) & (pred < 130)) |
        ((ref > 130) & (pred > 70) & (pred < 130))
    )
    
    # Zone E: dangerous
    zone_e = ~zone_a & ~zone_b & ~zone_c & ~zone_d
    
    zones[zone_a] = 'A'
    zones[zone_b] = 'B'
    zones[zone_c] = 'C'
    zones[zone_d] = 'D'
    zones[zone_e] = 'E'
    
    counts = pd.Series(zones).value_counts()
    return {k: counts.get(k, 0)/len(ref) for k in ['A', 'B', 'C', 'D', 'E']}

def main():
    config = load_config()
    data_dir = Path(config["paths"]["data_processed"])
    models_dir = Path(config["forecast"]["models_dir"])
    fig_dir = Path(config["paths"]["reports"]) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # Load models
    models = joblib.load(models_dir / "forecaster_v1.joblib")
    with open(models_dir / "forecaster_v1_meta.json", "r") as f:
        meta = json.load(f)
        
    df = pd.read_parquet(data_dir / "features.parquet")
    targets_df = pd.read_parquet(data_dir / "forecast_targets.parquet")
    
    df = df.merge(targets_df, on=["patient_id", "timestamp"])
    val_df = df[df["split"] == "val"].copy()
    train_df = df[df["split"] == "train"].copy()
    
    X_val = val_df[meta["features"]]
    horizons = meta["horizons"]
    
    # Predictions
    preds_persist = models["persist"].predict_quantiles(X_val)
    preds_linear = models["linear"].predict_quantiles(X_val)
    preds_ridge = models["ridge"].predict_quantiles(X_val)
    preds_xgb = models["xgb"].predict_quantiles(X_val)
    
    # Get Train MAE for overfitting check
    X_train = train_df[meta["features"]]
    preds_train = models["xgb"].predict_quantiles(X_train)
    y_train_60 = train_df["target_delta_60m"].values
    mask_tr = ~np.isnan(y_train_60)
    train_mae_60 = np.mean(np.abs(y_train_60[mask_tr] - preds_train[mask_tr, horizons.index(60), 1]))
    
    y_val_dict = {h: val_df[f"target_delta_{h}m"] for h in horizons}
    
    # Fit conformal calibrator
    print("Fitting conformal calibrator on VAL...")
    xgb_pred_dict = {h: preds_xgb[:, i, :] for i, h in enumerate(horizons)}
    calibrator = ConformalCalibrator(horizons, meta["quantiles"], config["forecast"]["nominal_interval_coverage"])
    calibrator.fit(y_val_dict, xgb_pred_dict)
    
    with open(models_dir / "forecast_conformal_v1.json", "w") as f:
        json.dump({"q_hat": calibrator.q_hat}, f, indent=2)
        
    preds_xgb_cal = calibrator.apply(preds_xgb)
    
    metrics = []
    
    for i, h in enumerate(horizons):
        y = y_val_dict[h].values
        mask = ~np.isnan(y)
        y_valid = y[mask]
        
        # XGB uncalibrated and calibrated
        pred_xgb = preds_xgb[mask, i, :]
        pred_cal = preds_xgb_cal[mask, i, :]
        pred_med = pred_xgb[:, 1]
        
        # Baselines
        pred_p = preds_persist[mask, i, 1]
        pred_l = preds_linear[mask, i, 1]
        pred_r = preds_ridge[mask, i, 1]
        
        mae_xgb = np.mean(np.abs(y_valid - pred_med))
        mae_p = np.mean(np.abs(y_valid - pred_p))
        mae_l = np.mean(np.abs(y_valid - pred_l))
        mae_r = np.mean(np.abs(y_valid - pred_r))
        
        rmse_xgb = np.sqrt(np.mean((y_valid - pred_med)**2))
        bias = np.mean(pred_med - y_valid)
        r2 = 1 - (np.sum((y_valid - pred_med)**2) / np.sum((y_valid - np.mean(y_valid))**2))
        
        # Coverage
        cov_uncal = np.mean((y_valid >= pred_xgb[:, 0]) & (y_valid <= pred_xgb[:, 2]))
        cov_cal = np.mean((y_valid >= pred_cal[:, 0]) & (y_valid <= pred_cal[:, 2]))
        
        # Within 15%
        # Convert to absolute glucose
        curr_glu = val_df["glu_current"].values[mask]
        abs_true = curr_glu + y_valid
        abs_pred = curr_glu + pred_med
        within_15 = np.mean((np.abs(abs_true - abs_pred) <= 0.15 * abs_true) | ((abs_true < 100) & (np.abs(abs_true - abs_pred) <= 15)))
        
        metrics.append({
            "horizon": h,
            "mae_xgb": mae_xgb,
            "mae_persist": mae_p,
            "mae_linear": mae_l,
            "mae_ridge": mae_r,
            "rmse": rmse_xgb,
            "bias": bias,
            "r2": r2,
            "coverage_uncal": cov_uncal,
            "coverage_cal": cov_cal,
            "within_15pct": within_15
        })
        
        if h in [30, 60]:
            cg = clarke_error_grid(abs_true, abs_pred)
            print(f"Clarke Error Grid {h}m:", {k: f"{v:.2%}" for k, v in cg.items()})
            
    mdf = pd.DataFrame(metrics)
    print("\nVAL Metrics:")
    print(mdf.to_string())
    
    out_dict = {}
    for h in horizons:
        row = mdf[mdf['horizon'] == h].iloc[0]
        out_dict[f"{h}m"] = row.to_dict()
    out_dict["train_mae_60m"] = train_mae_60
    
    with open(config["paths"]["reports"] + "/metrics_forecast_val.json", "w") as f:
        json.dump(out_dict, f, indent=2)
        
    print(f"\nTRAIN MAE 60m: {train_mae_60:.2f} | VAL MAE 60m: {mdf[mdf['horizon']==60]['mae_xgb'].iloc[0]:.2f}")
    
    # 1. Plot MAE
    plt.figure(figsize=(8, 5))
    plt.plot(mdf["horizon"], mdf["mae_xgb"], 'o-', label="XGBoost")
    plt.plot(mdf["horizon"], mdf["mae_persist"], 'x--', label="Persistence")
    plt.plot(mdf["horizon"], mdf["mae_linear"], '+--', label="Linear")
    plt.title("Forecast MAE by Horizon (VAL)")
    plt.xlabel("Horizon (minutes)")
    plt.ylabel("MAE (mg/dL)")
    plt.legend()
    plt.savefig(fig_dir / "val_mae_by_horizon.png", dpi=150)
    plt.close()
    
    # 2. Plot Coverage
    plt.figure(figsize=(8, 5))
    plt.plot(mdf["horizon"], mdf["coverage_uncal"], 'o--', label="Uncalibrated")
    plt.plot(mdf["horizon"], mdf["coverage_cal"], 'o-', label="Calibrated")
    plt.axhline(0.8, color='r', linestyle=':', label="Nominal (80%)")
    plt.title("Interval Coverage by Horizon (VAL)")
    plt.xlabel("Horizon (minutes)")
    plt.ylabel("Coverage")
    plt.legend()
    plt.savefig(fig_dir / "val_coverage_by_horizon.png", dpi=150)
    plt.close()
    
    # 3. Pred vs Actual 60m
    plt.figure(figsize=(6, 6))
    idx = horizons.index(60)
    y_60 = y_val_dict[60].values
    mask_60 = ~np.isnan(y_60)
    curr_glu_60 = val_df["glu_current"].values[mask_60]
    plt.scatter(curr_glu_60 + y_60[mask_60], curr_glu_60 + preds_xgb[mask_60, idx, 1], alpha=0.1, s=2)
    plt.plot([0, 400], [0, 400], 'k--')
    plt.xlim(40, 400); plt.ylim(40, 400)
    plt.xlabel("Actual 60m Future (mg/dL)")
    plt.ylabel("Predicted 60m Future (mg/dL)")
    plt.title("60-min Forecast Pred vs Actual (VAL)")
    plt.savefig(fig_dir / "val_pred_vs_actual_60m.png", dpi=150)
    plt.close()
    
    # 4. Example forecasts
    plt.figure(figsize=(15, 10))
    np.random.seed(42)
    valid_idx = np.where(mask_60)[0]
    ex_idx = np.random.choice(valid_idx, 6, replace=False)
    for i, ex in enumerate(ex_idx):
        plt.subplot(2, 3, i+1)
        pat = val_df.iloc[ex]["patient_id"]
        ts = pd.to_datetime(val_df.iloc[ex]["timestamp"])
        pat_df = val_df[(val_df["patient_id"] == pat) & 
                        (pd.to_datetime(val_df["timestamp"]) >= ts - pd.Timedelta(hours=2)) &
                        (pd.to_datetime(val_df["timestamp"]) <= ts + pd.Timedelta(minutes=120))].copy()
        
        plt.plot(pd.to_datetime(pat_df["timestamp"]), pat_df["glu_current"], 'k.-', alpha=0.5, label="Actual")
        curr_g = val_df.iloc[ex]["glu_current"]
        plt.plot([ts], [curr_g], 'ko')
        
        xs = [ts] + [ts + pd.Timedelta(minutes=h) for h in horizons]
        ys_med = [curr_g] + list(curr_g + preds_xgb_cal[ex, :, 1])
        ys_low = [curr_g] + list(curr_g + preds_xgb_cal[ex, :, 0])
        ys_high = [curr_g] + list(curr_g + preds_xgb_cal[ex, :, 2])
        
        plt.plot(xs, ys_med, 'b*-', label="Forecast")
        plt.fill_between(xs, ys_low, ys_high, color='b', alpha=0.2)
        plt.title(f"Patient {pat}")
        plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(fig_dir / "val_example_forecasts.png", dpi=150)
    plt.close()
    
if __name__ == "__main__":
    main()
