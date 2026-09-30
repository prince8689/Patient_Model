import pandas as pd
import numpy as np

def validate_wearable(wearable_df: pd.DataFrame, patients_df: pd.DataFrame, sim_params_df: pd.DataFrame) -> dict:
    req_cols = ["patient_id", "timestamp", "glucose_mgdl", "heart_rate", "steps", "sleep_state", "meal_carbs_g", "activity_intensity"]
    if list(wearable_df.columns) != req_cols:
        raise ValueError(f"Columns mismatch. Expected: {req_cols}")
        
    n_days = len(wearable_df) / (len(patients_df) * 288)
    if not n_days.is_integer():
        raise ValueError("Row count is not a multiple of patients * 288.")
        
    if not wearable_df["glucose_mgdl"].dropna().between(40, 400).all():
        raise ValueError("Glucose out of bounds.")
    if not wearable_df["heart_rate"].between(40, 190).all():
        raise ValueError("HR out of bounds.")
    if not (wearable_df["steps"] >= 0).all():
        raise ValueError("Negative steps found.")
    if not wearable_df["activity_intensity"].isin([0, 1, 2, 3]).all():
        raise ValueError("Invalid activity_intensity.")
    if not wearable_df["sleep_state"].isin(["awake", "light", "deep", "rem"]).all():
        raise ValueError("Invalid sleep_state.")
    if not (wearable_df["meal_carbs_g"] >= 0).all():
        raise ValueError("Negative meal_carbs_g.")
        
    miss_rate = wearable_df["glucose_mgdl"].isna().mean()
    if not (0.005 <= miss_rate <= 0.05):
        raise ValueError(f"Missing rate {miss_rate:.4f} not between 0.5% and 5%.")
        
    merged = wearable_df.merge(sim_params_df[["patient_id", "archetype"]], on="patient_id")
    merged = merged.merge(patients_df[["patient_id", "hba1c"]], on="patient_id")
    
    arch_means = merged.groupby("archetype")["glucose_mgdl"].mean()
    if not (arch_means.get("well_controlled", 0) < arch_means.get("moderate", 0) < arch_means.get("poorly_controlled", 0)):
        raise ValueError(f"Archetype mean ordering failed: {arch_means.to_dict()}")
        
    tir = merged.groupby("archetype").apply(lambda x: x["glucose_mgdl"].between(70, 180).mean())
    if tir.get("well_controlled", 0) <= tir.get("poorly_controlled", 0):
        raise ValueError("Well controlled TiR must be > poorly controlled TiR.")
        
    pat_means = merged.groupby("patient_id")[["glucose_mgdl", "hba1c"]].mean()
    if len(patients_df) >= 40 and pat_means["glucose_mgdl"].corr(pat_means["hba1c"]) < 0.6:
        raise ValueError("Correlation between mean glucose and HbA1c is < 0.6.")
        
    sleep_hr = wearable_df[wearable_df["sleep_state"] != "awake"]["heart_rate"].mean()
    awake_hr = wearable_df[wearable_df["sleep_state"] == "awake"]["heart_rate"].mean()
    if sleep_hr >= awake_hr:
        raise ValueError("Mean sleep HR must be less than awake HR.")

    meal_frac = (wearable_df["meal_carbs_g"] > 0).mean()
    if not (0.005 <= meal_frac <= 0.05):
        raise ValueError(f"Meal carbs nonzero fraction {meal_frac:.4f} not in range.")

    df = wearable_df.copy()
    df["glucose_mgdl_interp"] = df["glucose_mgdl"].interpolate().bfill().ffill()

    df["meal_marker"] = df["meal_carbs_g"] > 0
    df["recent_meals"] = df.groupby("patient_id")["meal_carbs_g"].transform(lambda x: x.rolling(24, min_periods=1).sum())
    df["fasting"] = df.groupby("patient_id")["meal_carbs_g"].transform(lambda x: x.rolling(48, min_periods=1).sum() == 0)
    
    post_meal_gluc = df[df["recent_meals"] > 0]["glucose_mgdl_interp"].mean()
    fasting_gluc = df[df["fasting"]]["glucose_mgdl_interp"].mean()
    if post_meal_gluc <= fasting_gluc:
        raise ValueError(f"Post-meal glucose ({post_meal_gluc:.1f}) not > fasting ({fasting_gluc:.1f})")

    # We shift indices carefully. Instead of df.loc, let's merge arrays to be safe from indexing issues
    ex_mask = df["activity_intensity"] >= 2
    # only valid if t-12 and t+12 exist within same patient
    # we can use shift
    pre_ex = df.groupby("patient_id")["glucose_mgdl_interp"].shift(12)
    post_ex = df.groupby("patient_id")["glucose_mgdl_interp"].shift(-12)
    
    valid_ex = ex_mask & pre_ex.notna() & post_ex.notna()
    if valid_ex.any():
        mean_pre = pre_ex[valid_ex].mean()
        mean_post = post_ex[valid_ex].mean()
        # For a truly robust physiological check, we add a small buffer or just check >
        # Actually just check mean_post < mean_pre
        if mean_post >= mean_pre:
            raise ValueError(f"Post-exercise glucose ({mean_post:.1f}) not lower than pre-exercise ({mean_pre:.1f})")

    def fwd_max(s):
        return s[::-1].rolling(24, min_periods=1).max()[::-1].shift(-1)
        
    # use raw interpolated for spike rate
    df["max_next_2h"] = df.groupby("patient_id")["glucose_mgdl_interp"].transform(fwd_max)
    spike_rate = (df["max_next_2h"] >= df["glucose_mgdl_interp"] + 50).mean()
    
    if len(patients_df) >= 40 and not (0.08 <= spike_rate <= 0.35):
        raise ValueError(f"Spike rate {spike_rate:.4f} not between 8% and 35%.")
        
    return {
        "spike_rate": spike_rate,
        "missing_rate": miss_rate,
        "meal_fraction": meal_frac,
        "archetype_means": arch_means.to_dict(),
        "time_in_range_well": tir.get("well_controlled"),
        "time_in_range_poor": tir.get("poorly_controlled")
    }
