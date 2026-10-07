import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

sys.path.append(str(Path(__file__).parent.parent))
from src.simulator.personalization import estimate_parameters
from src.utils.config import load_config


def main():
    config = load_config()
    data_dir = Path(config["paths"]["data_processed"])
    
    splits = pd.read_csv(data_dir / "splits.csv")
    train_patients = splits[splits["split"] == "train"]["patient_id"].values
    
    ehr_df = pd.read_csv(Path(config["paths"]["data_raw"]) / "patients.csv")
    
    maps = []
    valid_patients = []
    
    print(f"Fitting prior on {len(train_patients)} TRAIN patients...")
    for i, pid in enumerate(train_patients):
        history_file = data_dir / "wearable" / f"{pid}.parquet"
        if not history_file.exists():
            history_file = Path(config["paths"]["data_raw"]) / "wearable.csv"
            history_df = pd.read_csv(history_file)
            history_df = history_df[history_df["patient_id"] == pid].copy()
        else:
            history_df = pd.read_parquet(history_file)
            
        prof = ehr_df[ehr_df["patient_id"] == pid].iloc[0].to_dict()
        
        # Estimate without prior
        post = estimate_parameters(history_df, prof, prior={}, config=config)
        maps.append(post.mean)
        valid_patients.append(pid)
        print(f"  [{i+1}/{len(train_patients)}] {pid}: {post.mean}")
        
    map_df = pd.DataFrame(maps, index=valid_patients)
    
    features = ["age", "bmi", "hba1c", "diabetes_duration_years", "on_insulin", "on_metformin", "hypertension"]
    
    X = ehr_df.set_index("patient_id").loc[valid_patients][features].fillna(0.0).values
    Y = map_df.values
    
    ridge = Ridge(alpha=1.0)
    ridge.fit(X, Y)
    
    residuals = Y - ridge.predict(X)
    cov = np.cov(residuals, rowvar=False)
    
    prior_data = {
        "coef": ridge.coef_.tolist(),
        "intercept": ridge.intercept_.tolist(),
        "cov": cov.tolist(),
        "features": features,
        "param_names": list(map_df.columns),
        "train_patients_count": len(valid_patients)
    }
    
    prior_path = Path(config["whatif"]["prior_path"])
    prior_path.parent.mkdir(parents=True, exist_ok=True)
    with open(prior_path, "w") as f:
        json.dump(prior_data, f, indent=2)
        
    print(f"Saved prior to {prior_path}")

if __name__ == "__main__":
    main()
