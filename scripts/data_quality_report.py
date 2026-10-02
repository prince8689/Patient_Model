import json
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config


def main():
    config = load_config()
    raw_dir = Path(config["paths"]["data_raw"])
    proc_dir = Path(config["paths"]["data_processed"])
    
    wearable = pd.read_csv(raw_dir / "wearable.csv", parse_dates=["timestamp"])
    labels = pd.read_csv(proc_dir / "labels.csv")
    splits = pd.read_csv(proc_dir / "splits.csv")
    
    merged = labels.merge(splits, on="patient_id")
    
    n_rows = len(wearable)
    n_pats = wearable["patient_id"].nunique()
    start_dt = str(wearable["timestamp"].min())
    end_dt = str(wearable["timestamp"].max())
    
    missing_pct = (wearable.isna().mean() * 100).to_dict()
    
    gluc = wearable["glucose_mgdl"].dropna()
    g_mean = float(gluc.mean())
    g_sd = float(gluc.std())
    g_min = float(gluc.min())
    g_max = float(gluc.max())
    g_low = float((gluc < 70).mean() * 100)
    g_tir = float(gluc.between(70, 180).mean() * 100)
    g_high = float((gluc > 180).mean() * 100)
    
    overall_pos = float(labels[labels["valid"] == 1]["spike_next_2h"].mean() * 100)
    split_pos = {}
    for s in ["train", "val", "test"]:
        s_df = merged[(merged["split"] == s) & (merged["valid"] == 1)]
        split_pos[s] = float(s_df["spike_next_2h"].mean() * 100)
        
    dupes = int(wearable.duplicated(subset=["patient_id", "timestamp"]).sum())
    
    miss_mask = wearable["glucose_mgdl"].isna()
    gap_groups = (miss_mask != miss_mask.shift()).cumsum()
    gap_lens = miss_mask.groupby(gap_groups).sum()
    max_gap = int(gap_lens.max() * config["sampling_interval_minutes"])
    
    report = {
        "rows": n_rows,
        "patients": n_pats,
        "date_range": [start_dt, end_dt],
        "missing_pct": missing_pct,
        "glucose": {
            "mean": g_mean, "sd": g_sd, "min": g_min, "max": g_max,
            "pct_below_70": g_low, "pct_70_180": g_tir, "pct_above_180": g_high
        },
        "class_balance_overall_pct": overall_pos,
        "class_balance_splits_pct": split_pos,
        "duplicate_timestamps": dupes,
        "max_glucose_gap_mins": max_gap
    }
    
    with open("docs/data_quality.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
