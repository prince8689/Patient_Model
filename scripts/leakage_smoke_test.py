import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import xgboost as xgb

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.features.registry import FEATURE_REGISTRY

def main():
    config = load_config()
    feat_path = Path(config["features"]["features_path"])
    
    print("Loading features...")
    df = pd.read_parquet(feat_path)
    
    features = [f["name"] for f in FEATURE_REGISTRY]
    
    train_mask = (df["split"] == "train") & (df["valid"] == 1)
    val_mask = (df["split"] == "val") & (df["valid"] == 1)
    
    X_train = df.loc[train_mask, features]
    y_train = df.loc[train_mask, "spike_next_2h"]
    
    X_val = df.loc[val_mask, features]
    y_val = df.loc[val_mask, "spike_next_2h"]
    
    print(f"Train size: {len(X_train)}, Val size: {len(X_val)}")
    
    model = xgb.XGBClassifier(n_estimators=100, max_depth=4, random_state=42)
    print("Training real smoke test...")
    model.fit(X_train, y_train)
    
    val_preds = model.predict_proba(X_val)[:, 1]
    val_auc = roc_auc_score(y_val, val_preds)
    
    print(f"\n--- REAL LABELS SMOKE TEST ---")
    print(f"Val ROC-AUC: {val_auc:.4f}")
    if val_auc > 0.98:
        print(">> WARNING: Val AUC > 0.98. Suspicious leakage! Investigate.")
    elif val_auc < 0.65:
        print(">> WARNING: Val AUC < 0.65. Features are weak or broken.")
    else:
        print(">> OK: Val AUC is in plausible range.")
        
    print("\n--- SHUFFLED LABELS SMOKE TEST ---")
    shuffled_y_train = df.loc[train_mask].groupby("patient_id")["spike_next_2h"].transform(np.random.permutation)
    
    model_shuff = xgb.XGBClassifier(n_estimators=100, max_depth=4, random_state=42)
    model_shuff.fit(X_train, shuffled_y_train)
    
    shuff_preds = model_shuff.predict_proba(X_val)[:, 1]
    shuff_auc = roc_auc_score(y_val, shuff_preds)
    
    print(f"Shuffled Val ROC-AUC: {shuff_auc:.4f}")
    if abs(shuff_auc - 0.5) > 0.05:
        print(">> WARNING: Shuffled AUC is not near 0.5. The pipeline might have a hidden leak!")
    else:
        print(">> OK: Shuffled AUC near 0.5. No hidden leak detected.")
        
    print("\nNOTE: These numbers are a sanity check and NOT the final model results.")

if __name__ == "__main__":
    main()
