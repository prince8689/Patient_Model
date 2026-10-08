import pandas as pd
from pathlib import Path

def load_real_glucose():
    base_dir = Path("data/processed")
    df = pd.read_csv(base_dir / "real_glucose.csv")
    return df

def get_patient_group_map(patient_ids):
    """
    Returns a mapping from patient_id to a unique group identifier.
    Currently, there are no duplicates identified, so the map is the identity mapping.
    """
    return {pid: pid for pid in patient_ids}
