import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.data_gen.labels import make_labels
from src.data_gen.splits import make_patient_splits, assert_no_patient_overlap

def main():
    config = load_config()
    raw_dir = Path(config["paths"]["data_raw"])
    proc_dir = Path(config["paths"]["data_processed"])
    proc_dir.mkdir(parents=True, exist_ok=True)
    
    patients_df = pd.read_csv(raw_dir / "patients.csv")
    wearable_df = pd.read_csv(raw_dir / "wearable.csv")
    
    print("Building labels...")
    labels_df = make_labels(wearable_df, config)
    labels_df.to_csv(proc_dir / "labels.csv", index=False)
    
    print("Building splits...")
    splits_df = make_patient_splits(patients_df, config)
    assert_no_patient_overlap(splits_df)
    splits_df.to_csv(proc_dir / "splits.csv", index=False)
    
    # Stats
    n_total = len(labels_df)
    n_valid = labels_df["valid"].sum()
    valid_pct = n_valid / n_total * 100
    pos_rate = labels_df[labels_df["valid"] == 1]["spike_next_2h"].mean() * 100
    
    print(f"Valid rows: {n_valid} / {n_total} ({valid_pct:.1f}%)")
    print(f"Overall positive rate (valid rows): {pos_rate:.2f}%")
    
    merged = labels_df.merge(splits_df, on="patient_id")
    pat_splits = splits_df["split"].value_counts()
    
    print("\nStats per split:")
    for sp in ["train", "val", "test"]:
        sp_df = merged[(merged["split"] == sp) & (merged["valid"] == 1)]
        sp_pos = sp_df["spike_next_2h"].mean() * 100
        sp_pats = pat_splits.get(sp, 0)
        sp_hba1c = patients_df[patients_df["patient_id"].isin(splits_df[splits_df["split"]==sp]["patient_id"])]["hba1c"].mean()
        print(f"  {sp}: {sp_pats} patients, {sp_pos:.2f}% positive, mean HbA1c: {sp_hba1c:.2f}%")

if __name__ == "__main__":
    main()
