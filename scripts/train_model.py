import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import xgboost as xgb

sys.path.append(str(Path(__file__).parent.parent))
from src.features.registry import FEATURE_REGISTRY
from src.utils.config import load_config


def main():
    config = load_config()
    feat_path = Path(config["paths"]["data_processed"]) / "features.parquet"
    models_path = Path(config["paths"]["models"])
    models_path.mkdir(parents=True, exist_ok=True)
    
    print("Loading features...")
    df = pd.read_parquet(feat_path)
    
    features = [f["name"] for f in FEATURE_REGISTRY]
    
    train_mask = (df["split"] == "train") & (df["valid"] == 1)
    
    X_train = df.loc[train_mask, features]
    y_train = df.loc[train_mask, "spike_next_2h"]
    
    print(f"Training on {len(X_train)} rows with {len(features)} features...")
    
    # Tuned hyperparameters simulation
    hyperparams = {
        "n_estimators": 100,
        "max_depth": 5,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "n_jobs": -1
    }
    
    model = xgb.XGBClassifier(**hyperparams)
    model.fit(X_train, y_train)
    
    print("Saving model...")
    joblib.dump(model, models_path / "xgb_v1.joblib")
    
    meta = {
        "features": features,
        "hyperparameters": hyperparams,
        "model_version": "v1"
    }
    with open(models_path / "xgb_v1_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
        
    print("Done. Model saved.")

if __name__ == "__main__":
    main()
