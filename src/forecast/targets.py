import pandas as pd
import numpy as np

def make_forecast_targets(wearable_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Computes delta targets for forecasting.
    delta = future_glucose - current_glucose
    Only rows where both are valid get a valid flag.
    """
    df = wearable_df.sort_values(["patient_id", "timestamp"]).copy()
    interval = config["sampling_interval_minutes"]
    horizons = config["forecast"]["horizons_minutes"]
    
    # We output patient_id, timestamp, and the targets
    out = df[["patient_id", "timestamp"]].copy()
    
    for h in horizons:
        steps = int(h / interval)
        # Shift negatively to get future values
        future_glu = df.groupby("patient_id")["glucose_mgdl"].shift(-steps)
        current_glu = df["glucose_mgdl"]
        
        delta = future_glu - current_glu
        valid = future_glu.notna() & current_glu.notna()
        
        out[f"target_delta_{h}m"] = delta
        out[f"target_valid_{h}m"] = valid.astype(int)
        
    return out
