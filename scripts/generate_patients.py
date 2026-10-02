import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_gen.patients import generate_patients
from src.data_gen.validate_patients import validate_patients
from src.utils.config import load_config


def main():
    config = load_config()
    n_patients = config["n_patients"]
    seed = config["random_seed"]
    
    print(f"Generating data for {n_patients} patients (seed={seed})...")
    patients_df, sim_params_df = generate_patients(n_patients, seed)
    
    print("Validating data...")
    try:
        stats = validate_patients(patients_df, sim_params_df)
    except ValueError as e:
        print(f"Validation failed: {e}")
        sys.exit(1)
    
    out_dir_raw = Path(config["paths"]["data_raw"])
    out_dir_raw.mkdir(parents=True, exist_ok=True)
    
    patients_path = out_dir_raw / "patients.csv"
    sim_params_path = out_dir_raw / "patient_sim_params.csv"
    
    patients_df.to_csv(patients_path, index=False)
    sim_params_df.to_csv(sim_params_path, index=False)
    
    print(f"Data saved to {patients_path} and {sim_params_path}")
    print("\nSummary Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
