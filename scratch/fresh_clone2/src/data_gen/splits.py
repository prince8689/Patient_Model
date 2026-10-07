import numpy as np
import pandas as pd


def make_patient_splits(patients_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    rng = np.random.default_rng(config["random_seed"])
    
    pdf = patients_df.copy()
    pdf["hba1c_tertile"] = pd.qcut(pdf["hba1c"], q=3, labels=["low", "mid", "high"])
    
    train_frac = config["split"]["train"]
    val_frac = config["split"]["val"]
    
    splits = []
    
    for tertile in ["low", "mid", "high"]:
        t_pats = pdf[pdf["hba1c_tertile"] == tertile]["patient_id"].values
        rng.shuffle(t_pats)
        n = len(t_pats)
        
        n_train = int(np.round(n * train_frac))
        n_val = int(np.round(n * val_frac))
        
        train_pats = t_pats[:n_train]
        val_pats = t_pats[n_train:n_train+n_val]
        test_pats = t_pats[n_train+n_val:]
        
        for p in train_pats: splits.append({"patient_id": p, "split": "train"})
        for p in val_pats: splits.append({"patient_id": p, "split": "val"})
        for p in test_pats: splits.append({"patient_id": p, "split": "test"})
        
    splits_df = pd.DataFrame(splits)
    return splits_df

def assert_no_patient_overlap(splits_df: pd.DataFrame):
    counts = splits_df["patient_id"].value_counts()
    if (counts > 1).any():
        overlap = counts[counts > 1].index.tolist()
        raise ValueError(f"Patient overlap detected for: {overlap}")
