import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config

def main():
    config = load_config()
    proc_dir = Path(config["paths"]["data_processed"])
    raw_dir = Path(config["paths"]["data_raw"])
    
    labels = pd.read_csv(proc_dir / "labels.csv", parse_dates=["timestamp"])
    splits = pd.read_csv(proc_dir / "splits.csv")
    wearable = pd.read_csv(raw_dir / "wearable.csv", parse_dates=["timestamp"])
    
    merged = labels.merge(splits, on="patient_id").merge(wearable, on=["patient_id", "timestamp"]).sort_values(["patient_id", "timestamp"])
    
    merged["carbs_60m"] = merged.groupby("patient_id")["meal_carbs_g"].transform(lambda x: x.rolling(12, min_periods=1).sum())
    
    meal_times = merged[merged["meal_carbs_g"] > 0][["patient_id", "timestamp"]].copy()
    meal_times["last_meal"] = meal_times["timestamp"]
    merged = merged.sort_values("timestamp")
    meal_times = meal_times.sort_values("timestamp")
    merged = pd.merge_asof(merged, meal_times, by="patient_id", on="timestamp", direction="backward")
    merged["mins_since_meal"] = (merged["timestamp"] - merged["last_meal"]).dt.total_seconds() / 60.0
    merged["mins_since_meal"] = merged["mins_since_meal"].fillna(360)
    
    merged["hour"] = merged["timestamp"].dt.hour
    
    merged["glucose_30m_ago"] = merged.groupby("patient_id")["glucose_mgdl"].shift(6)
    merged["delta_30m"] = merged["glucose_mgdl"] - merged["glucose_30m_ago"]
    
    valid_val = merged[(merged["valid"] == 1) & (merged["split"] == "val")].dropna(subset=["delta_30m", "glucose_mgdl"])
    
    print("Learnability Check (Validation Split)")
    print("-" * 40)
    
    y = valid_val["spike_next_2h"]
    features = {
        "Carbs last 60m": valid_val["carbs_60m"],
        "Mins since meal": valid_val["mins_since_meal"],
        "Current glucose": valid_val["glucose_mgdl"],
        "Hour of day": valid_val["hour"],
        "Delta 30m": valid_val["delta_30m"]
    }
    
    best_auc = 0
    for name, x in features.items():
        auc = roc_auc_score(y, x)
        direction = "+"
        if auc < 0.5:
            auc = 1 - auc
            direction = "-"
        print(f"{name:20s}: AUC = {auc:.3f} ({direction})")
        best_auc = max(best_auc, auc)
        
    print("-" * 40)
    print(f"Best single-feature AUC: {best_auc:.3f}")
    
    if best_auc > 0.95:
        print("WARNING: Task is too trivial (>0.95 AUC).")
    elif best_auc < 0.60:
        print("WARNING: Task is nearly unpredictable (<0.60 AUC).")
    else:
        print("Learnability is within the acceptable range (0.60 - 0.90).")

if __name__ == "__main__":
    main()
