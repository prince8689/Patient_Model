import pandas as pd
import os
from pathlib import Path

def load_real_glucose(include_test=False):
    base_dir = Path("data/processed")
    df = pd.read_csv(base_dir / "real_glucose.csv")
    
    if include_test:
        if os.environ.get("ALLOW_REAL_TEST") != "1":
            raise PermissionError("Cannot load real test data unless ALLOW_REAL_TEST=1 is set")
        return df
        
    # Filter out test rows
    splits = pd.read_csv(base_dir / "real_splits.csv")
    test_pids = splits[splits['split'] == 'test']['patient_id'].astype(str).tolist()
    df['patient_id'] = df['patient_id'].astype(str)
    
    df = df[~df['patient_id'].isin(test_pids)].copy()
    return df
