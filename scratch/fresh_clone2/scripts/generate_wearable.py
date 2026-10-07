import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.data_gen.validate_wearable import validate_wearable
from src.data_gen.wearable import generate_wearable
from src.utils.config import load_config


def main():
    config = load_config()
    raw_dir = Path(config["paths"]["data_raw"])
    
    patients_df = pd.read_csv(raw_dir / "patients.csv")
    sim_params_df = pd.read_csv(raw_dir / "patient_sim_params.csv")
    
    print("Generating wearable time-series...")
    wearable_df = generate_wearable(patients_df, sim_params_df, config)
    
    print("Validating data...")
    try:
        stats = validate_wearable(wearable_df, patients_df, sim_params_df)
    except ValueError as e:
        print(f"Validation failed: {e}")
        sys.exit(1)
        
    out_path = raw_dir / "wearable.csv"
    wearable_df.to_csv(out_path, index=False)
    
    print(f"Saved {len(wearable_df)} rows to {out_path}")
    for k, v in stats.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
