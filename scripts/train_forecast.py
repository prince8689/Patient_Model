import sys
import json
import joblib
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.forecast.baselines import PersistenceForecaster, LinearExtrapolationForecaster, RidgeForecaster
from src.forecast.model import GlucoseForecaster

def main():
    config = load_config()
    data_dir = Path(config["paths"]["data_processed"])
    models_dir = Path(config["forecast"]["models_dir"])
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    features_df = pd.read_parquet(data_dir / "features.parquet")
    splits_df = pd.read_csv(data_dir / "splits.csv")
    targets_df = pd.read_parquet(data_dir / "forecast_targets.parquet")
    
    # Merge splits
    df = features_df.merge(targets_df, on=["patient_id", "timestamp"])
    
    train_df = df[df["split"] == "train"]
    print(f"Train rows: {len(train_df)}")
    
    # Drop columns not used as features
    drop_cols = ["patient_id", "timestamp", "split", "fold", "valid", "spike_next_2h", "label", "baseline_insulin_sensitivity"] + [c for c in df.columns if c.startswith("target_")]
    X_train = train_df.drop(columns=drop_cols, errors="ignore")
    
    horizons = config["forecast"]["horizons_minutes"]
    quantiles = config["forecast"]["quantiles"]
    y_train_dict = {h: train_df[f"target_delta_{h}m"] for h in horizons}
    groups = train_df["patient_id"]
    
    print("Training Baselines...")
    persist = PersistenceForecaster(horizons, quantiles)
    persist.fit(X_train, y_train_dict)
    
    linear = LinearExtrapolationForecaster(horizons, quantiles)
    linear.fit(X_train, y_train_dict)
    
    ridge = RidgeForecaster(horizons, quantiles)
    ridge.fit(X_train, y_train_dict)
    
    print("Training XGBoost Quantile Forecaster...")
    model = GlucoseForecaster(config)
    model.fit(X_train, y_train_dict, groups)
    
    # Save artifacts
    print("Saving models...")
    joblib.dump({
        "persist": persist,
        "linear": linear,
        "ridge": ridge,
        "xgb": model
    }, models_dir / "forecaster_v1.joblib")
    
    meta = {
        "features": list(X_train.columns),
        "horizons": horizons,
        "quantiles": quantiles,
        "seed": config["random_seed"],
        "version": "v1"
    }
    with open(models_dir / "forecaster_v1_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
        
    print("Done training.")

if __name__ == "__main__":
    main()
