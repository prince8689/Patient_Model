import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.features.engineering import build_features
from src.features.registry import assert_no_forbidden, get_feature_names
from src.utils.config import load_config


def main():
    config = load_config()
    raw_dir = Path(config["paths"]["data_raw"])
    proc_dir = Path(config["paths"]["data_processed"])
    
    print("Loading data...")
    wearable = pd.read_csv(raw_dir / "wearable.csv", parse_dates=["timestamp"])
    patients = pd.read_csv(raw_dir / "patients.csv")
    labels = pd.read_csv(proc_dir / "labels.csv", parse_dates=["timestamp"])
    splits = pd.read_csv(proc_dir / "splits.csv")
    
    print("Building features (this might take a minute)...")
    feats = build_features(wearable, patients, config)
    
    assert_no_forbidden(get_feature_names())
    for col in feats.columns:
        if col not in ["patient_id", "timestamp"]:
            if col in ["spike_next_2h", "future_max_glucose", "valid", "split"]:
                raise ValueError(f"Forbidden column {col} in features!")
                
    # Merge
    print("Merging with labels and splits...")
    merged = feats.merge(splits, on="patient_id", how="left")
    merged = merged.merge(labels[["patient_id", "timestamp", "valid", "spike_next_2h"]], on=["patient_id", "timestamp"], how="left")
    
    assert len(merged) == len(wearable), "Row count mismatch after merge!"
    assert merged.duplicated(subset=["patient_id", "timestamp"]).sum() == 0, "Duplicates found!"
    
    out_path = Path(config["features"]["features_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    cols = ["patient_id", "timestamp", "split", "valid", "spike_next_2h"] + get_feature_names()
    final_df = merged[cols]
    
    print(f"Saving to {out_path} ...")
    final_df.to_parquet(out_path, index=False)
    
    n_feats = len(get_feature_names())
    print("\nFeature build complete.")
    print(f"Features generated: {n_feats}")
    print(f"Total rows: {len(final_df)}")
    print(f"Size in memory: {final_df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
    
    print("\nTraining-eligible rows (valid=1) per split:")
    print(final_df[final_df["valid"] == 1]["split"].value_counts())

if __name__ == "__main__":
    main()
