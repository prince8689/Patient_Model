import pandas as pd
import numpy as np

def make_labels(wearable_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Creates prediction labels for the glucose spike task.
    """
    horizon_mins = config["prediction_horizon_minutes"]
    interval_mins = config["sampling_interval_minutes"]
    threshold = config["spike_threshold_mgdl"]
    min_cov = config["label_min_future_coverage"]
    
    horizon_steps = int(horizon_mins / interval_mins)
    
    df = wearable_df[["patient_id", "timestamp", "glucose_mgdl"]].copy()
    
    def calc_future_max(s):
        return s[::-1].rolling(horizon_steps, min_periods=1).max()[::-1].shift(-1)
        
    def calc_future_count(s):
        return s.notna()[::-1].rolling(horizon_steps, min_periods=1).sum()[::-1].shift(-1)
        
    df["future_max_glucose"] = df.groupby("patient_id")["glucose_mgdl"].transform(calc_future_max)
    df["future_count"] = df.groupby("patient_id")["glucose_mgdl"].transform(calc_future_count)
    
    df["valid"] = 1
    df.loc[df["glucose_mgdl"].isna(), "valid"] = 0
    df.loc[df["future_count"] < (horizon_steps * min_cov), "valid"] = 0
    
    df["rev_idx"] = df.groupby("patient_id").cumcount(ascending=False)
    df.loc[df["rev_idx"] < horizon_steps, "valid"] = 0
    
    df["spike_next_2h"] = np.nan
    valid_mask = df["valid"] == 1
    df.loc[valid_mask, "spike_next_2h"] = (df.loc[valid_mask, "future_max_glucose"] >= df.loc[valid_mask, "glucose_mgdl"] + threshold).astype(int)
    
    return df[["patient_id", "timestamp", "valid", "spike_next_2h", "future_max_glucose"]]
