import pandas as pd
from pathlib import Path

def load_real_glucose():
    base_dir = Path("data/processed")
    df = pd.read_csv(base_dir / "real_glucose.csv")
    return df

