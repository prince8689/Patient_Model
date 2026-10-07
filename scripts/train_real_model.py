import json
import sys
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score
from sklearn.model_selection import GroupKFold

sys.path.append(str(Path(__file__).parent.parent))

def generate_features(df):
    df = df.sort_values(["patient_id", "timestamp"]).reset_index(drop=True)
    
    # 15 min grid
    df['glu_lag_15m'] = df.groupby('patient_id')['glucose_mgdl'].shift(1)
    df['glu_lag_30m'] = df.groupby('patient_id')['glucose_mgdl'].shift(2)
    df['glu_lag_60m'] = df.groupby('patient_id')['glucose_mgdl'].shift(4)
    
    df['glu_delta_15m'] = df['glucose_mgdl'] - df['glu_lag_15m']
    df['glu_delta_60m'] = df['glucose_mgdl'] - df['glu_lag_60m']
    
    roll = df.groupby('patient_id')['glucose_mgdl'].rolling(4, min_periods=1)
    df['glu_roll_mean_60m'] = roll.mean().reset_index(level=0, drop=True)
    df['glu_roll_std_60m'] = roll.std().reset_index(level=0, drop=True)
    df['glu_roll_max_60m'] = roll.max().reset_index(level=0, drop=True)
    
    return df

def main():
    print("Loading real data...")
    try:
        glucose = pd.read_csv("data/processed/real_glucose.csv")
    except FileNotFoundError:
        print("Real data not found. Please ensure harmonization has run.")
        sys.exit(1)
        
    glucose['timestamp'] = pd.to_datetime(glucose['timestamp'])
    
    print("Generating features...")
    df = generate_features(glucose)
    df = df.dropna(subset=['label'])
    
    features = [
        'glucose_mgdl', 'glu_lag_15m', 'glu_lag_30m', 'glu_lag_60m', 
        'glu_delta_15m', 'glu_delta_60m', 'glu_roll_mean_60m', 
        'glu_roll_std_60m', 'glu_roll_max_60m'
    ]
    
    df = df.dropna(subset=features)
    
    X = df[features]
    y = df['label']
    groups = df['patient_id']
    
    print(f"Total samples: {len(X)}")
    print(f"Unique patients: {groups.nunique()}")
    
    gkf = GroupKFold(n_splits=5)
    
    aucs = []
    aps = []
    
    fold = 1
    for train_idx, val_idx in gkf.split(X, y, groups):
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
        
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        preds = model.predict_proba(X_val)[:, 1]
        
        if len(np.unique(y_val)) > 1:
            auc = roc_auc_score(y_val, preds)
            ap = average_precision_score(y_val, preds)
            aucs.append(auc)
            aps.append(ap)
            print(f"Fold {fold}: AUC={auc:.4f}, AP={ap:.4f}")
        else:
            print(f"Fold {fold}: Only one class present in validation set.")
        fold += 1
        
    mean_auc = np.mean(aucs)
    mean_ap = np.mean(aps)
    
    print(f"\nCV Results (5-Fold Grouped by Patient):")
    print(f"Mean AUC: {mean_auc:.4f}")
    print(f"Mean AP:  {mean_ap:.4f}")
    
    # Save metrics report
    report = {
        "model": "XGBoost",
        "dataset": "ShanghaiT2DM_real",
        "validation_strategy": "GroupKFold (patient-wise)",
        "folds": 5,
        "n_samples": len(X),
        "n_patients": groups.nunique(),
        "metrics": {
            "mean_roc_auc": float(mean_auc),
            "mean_average_precision": float(mean_ap)
        },
        "features": features
    }
    
    with open("reports/metrics_real_model.json", "w") as f:
        json.dump(report, f, indent=4)
        
    print("Report saved to reports/metrics_real_model.json")

if __name__ == "__main__":
    main()
