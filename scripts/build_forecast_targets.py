import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.forecast.targets import make_forecast_targets

def main():
    config = load_config()
    df_wear = pd.read_csv(Path(config["paths"]["data_raw"]) / "wearable.csv")
    df_wear["timestamp"] = pd.to_datetime(df_wear["timestamp"])
    
    targets = make_forecast_targets(df_wear, config)
    out_path = Path(config["paths"]["data_processed"]) / "forecast_targets.parquet"
    targets.to_parquet(out_path, index=False)
    
    print(f"Saved forecast targets to {out_path}")
    
    # Summary
    horizons = config["forecast"]["horizons_minutes"]
    for h in horizons:
        valid_count = targets[f"target_valid_{h}m"].sum()
        delta_col = targets.loc[targets[f"target_valid_{h}m"] == 1, f"target_delta_{h}m"]
        print(f"Horizon {h}m: {valid_count} valid rows")
        if valid_count > 0:
            print(f"  Delta Mean: {delta_col.mean():.1f}, Std: {delta_col.std():.1f}")
            print(f"  Delta 10%: {delta_col.quantile(0.1):.1f}, 50%: {delta_col.median():.1f}, 90%: {delta_col.quantile(0.9):.1f}")
            
    # share of rows with missing current glucose
    missing_current = df_wear["glucose_mgdl"].isna().mean()
    print(f"Share of rows with missing current glucose: {missing_current:.2%}")

if __name__ == "__main__":
    main()
