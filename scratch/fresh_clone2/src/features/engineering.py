import numpy as np
import pandas as pd

from .registry import assert_no_forbidden, get_feature_names


def compute_cob_estimate(meal_carbs_series: pd.Series, peak_steps: int, duration_steps: int) -> pd.Series:
    """
    Computes Carbs on Board (COB) using a discrete triangular kernel.
    Absorption rate peaks at `peak_steps` and ends at `duration_steps`.
    """
    if duration_steps <= 0:
        return pd.Series(0, index=meal_carbs_series.index)
    kernel = np.zeros(duration_steps)
    for t in range(duration_steps):
        if t < peak_steps and peak_steps > 0:
            unabsorbed = 1.0 - 0.5 * (t / peak_steps) * (t / duration_steps)
        else:
            if duration_steps > peak_steps:
                unabsorbed = 0.5 * ((duration_steps - t) / (duration_steps - peak_steps))
            else:
                unabsorbed = 0.0
        kernel[t] = max(0, unabsorbed)
    
    carbs_arr = meal_carbs_series.fillna(0).values
    cob = np.convolve(carbs_arr, kernel, mode='full')[:len(carbs_arr)]
    return pd.Series(cob, index=meal_carbs_series.index)

def build_features_for_patient(wearable_patient_df: pd.DataFrame, patient_row: pd.Series, config: dict) -> pd.DataFrame:
    df = wearable_patient_df.copy().sort_values("timestamp").reset_index(drop=True)
    interval = config["sampling_interval_minutes"]
    f_conf = config["features"]
    
    out = pd.DataFrame()
    out["patient_id"] = df["patient_id"]
    out["timestamp"] = df["timestamp"]
    
    # A) Glucose - glu_
    g = df["glucose_mgdl"]
    out["glu_current"] = g
    for lag_m in f_conf["lag_minutes"]:
        lag_steps = int(lag_m / interval)
        out[f"glu_lag_{lag_m}m"] = g.shift(lag_steps)
        if lag_m in [5, 15, 30, 60]:
            out[f"glu_delta_{lag_m}m"] = g - out[f"glu_lag_{lag_m}m"]
            
    def calc_slope(s):
        s = s.dropna()
        if len(s) < 3: return np.nan
        x = np.arange(len(s)) * interval
        return np.polyfit(x, s.values, 1)[0]
    
    out["glu_slope_30m"] = g.rolling(7, min_periods=3).apply(calc_slope, raw=False)
    out["glu_slope_15m_prev"] = g.shift(3).rolling(4, min_periods=3).apply(calc_slope, raw=False)
    out["glu_slope_15m"] = g.rolling(4, min_periods=3).apply(calc_slope, raw=False)
    out["glu_accel"] = out["glu_slope_15m"] - out["glu_slope_15m_prev"]
    
    min_frac = f_conf["min_periods_fraction"]
    for w_m in f_conf["rolling_windows_minutes"]:
        w_steps = int(w_m / interval) + 1
        min_p = max(1, int(w_steps * min_frac))
        out[f"glu_roll_mean_{w_m}m"] = g.rolling(w_steps, min_periods=min_p).mean()
        out[f"glu_roll_std_{w_m}m"] = g.rolling(w_steps, min_periods=min_p).std()
        out[f"glu_roll_min_{w_m}m"] = g.rolling(w_steps, min_periods=min_p).min()
        out[f"glu_roll_max_{w_m}m"] = g.rolling(w_steps, min_periods=min_p).max()
        
    out["glu_range_60m"] = out["glu_roll_max_60m"] - out["glu_roll_min_60m"]
    
    w60_steps = int(60 / interval) + 1
    out["glu_above_180_frac_60m"] = (g > 180).rolling(w60_steps, min_periods=1).mean()
    out["glu_below_70_frac_60m"] = (g < 70).rolling(w60_steps, min_periods=1).mean()
    
    # B) Meals - meal_
    m = df["meal_carbs_g"].fillna(0)
    for w_m in f_conf["meal_windows_minutes"]:
        w_steps = int(w_m / interval) + 1
        out[f"meal_carbs_last_{w_m}m"] = m.rolling(w_steps, min_periods=1).sum()
        
    meal_mask = m > 0
    meal_idxs = df.index[meal_mask]
    
    # Efficient min since last
    last_meal_idx = pd.Series(np.nan, index=df.index)
    last_meal_idx.loc[meal_idxs] = meal_idxs
    last_meal_idx = last_meal_idx.ffill()
    mins = (df.index - last_meal_idx) * interval
        
    out["meal_min_since_last"] = mins.fillna(f_conf["max_minutes_since_meal"]).clip(upper=f_conf["max_minutes_since_meal"])
    out["meal_any_in_history"] = mins.notna().astype(int)
    
    # meal_last_carbs_g
    last_carbs = pd.Series(np.nan, index=df.index)
    last_carbs.loc[meal_idxs] = m.loc[meal_idxs]
    out["meal_last_carbs_g"] = last_carbs.ffill().fillna(0.0)
        
    w360_steps = int(360 / interval) + 1
    out["meal_count_last_6h"] = meal_mask.rolling(w360_steps, min_periods=1).sum()
    
    peak_steps = int(f_conf["carb_absorption_peak_minutes"] / interval)
    dur_steps = int(f_conf["carb_absorption_duration_minutes"] / interval)
    out["meal_cob_estimate"] = compute_cob_estimate(m, peak_steps, dur_steps)
    
    # C) Activity - act_
    a = df["activity_intensity"].fillna(0)
    out["act_current_intensity"] = a
    
    steps = df["steps"].fillna(0)
    for w_m in f_conf["activity_windows_minutes"]:
        w_steps = int(w_m / interval) + 1
        out[f"act_steps_last_{w_m}m"] = steps.rolling(w_steps, min_periods=1).sum()
        
    out["act_max_intensity_last_60m"] = a.rolling(w60_steps, min_periods=1).max()
    
    act_mask = a >= 2
    act_idxs = df.index[act_mask]
    last_act_idx = pd.Series(np.nan, index=df.index)
    last_act_idx.loc[act_idxs] = act_idxs
    last_act_idx = last_act_idx.ffill()
    act_mins = (df.index - last_act_idx) * interval
    
    out["act_min_since_moderate"] = act_mins.fillna(f_conf["max_minutes_since_activity"]).clip(upper=f_conf["max_minutes_since_activity"])
    
    # D) Heart rate - hr_
    hr = df["heart_rate"]
    out["hr_current"] = hr
    
    for w_m in [30, 60]:
        w_steps = int(w_m / interval) + 1
        out[f"hr_roll_mean_{w_m}m"] = hr.rolling(w_steps, min_periods=1).mean()
        if w_m == 30:
            out["hr_roll_std_30m"] = hr.rolling(w_steps, min_periods=1).std()
            
    out["hr_delta_30m"] = hr - hr.shift(int(30/interval))
    
    w24h_steps = int(24 * 60 / interval) + 1
    past_24h_median = hr.rolling(w24h_steps, min_periods=max(1, int(w24h_steps * min_frac))).median()
    out["hr_vs_personal_baseline"] = hr - past_24h_median
    
    # E) Sleep - sleep_
    slp = df["sleep_state"].fillna("awake")
    out["sleep_is_asleep"] = (slp != "awake").astype(int)
    for state in ["awake", "light", "deep", "rem"]:
        out[f"sleep_state_{state}"] = (slp == state).astype(int)
        
    w12h_steps = int(12 * 60 / interval) + 1
    out["sleep_minutes_last_12h"] = out["sleep_is_asleep"].rolling(w12h_steps, min_periods=1).sum() * interval
    
    deep_rem = out["sleep_state_deep"] + out["sleep_state_rem"]
    deep_rem_min = deep_rem.rolling(w12h_steps, min_periods=1).sum() * interval
    out["sleep_deep_rem_frac_last_12h"] = np.where(out["sleep_minutes_last_12h"] > 0, deep_rem_min / out["sleep_minutes_last_12h"], np.nan)
    
    wake_transitions = (slp.shift(1) != "awake") & (slp == "awake")
    wake_idxs = df.index[wake_transitions]
    last_wake_idx = pd.Series(np.nan, index=df.index)
    last_wake_idx.loc[wake_idxs] = wake_idxs
    last_wake_idx = last_wake_idx.ffill()
    wake_mins = (df.index - last_wake_idx) * interval
        
    out["sleep_min_since_wake"] = wake_mins.fillna(720).clip(upper=720)
    out.loc[out["sleep_is_asleep"] == 1, "sleep_min_since_wake"] = 0.0
    
    # F) Time - time_
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        dt_col = pd.to_datetime(df["timestamp"])
    else:
        dt_col = df["timestamp"]
    mins_mid = dt_col.dt.hour * 60 + dt_col.dt.minute
    out["time_hour_sin"] = np.sin(2 * np.pi * mins_mid / 1440)
    out["time_hour_cos"] = np.cos(2 * np.pi * mins_mid / 1440)
    dow = dt_col.dt.dayofweek
    out["time_dow_sin"] = np.sin(2 * np.pi * dow / 7)
    out["time_dow_cos"] = np.cos(2 * np.pi * dow / 7)
    out["time_is_weekend"] = (dow >= 5).astype(int)
    
    # G) Static EHR - ehr_
    out["ehr_age"] = patient_row["age"]
    out["ehr_sex_male"] = 1 if patient_row["sex"] == "M" else 0
    out["ehr_bmi"] = patient_row["bmi"]
    out["ehr_hba1c"] = patient_row["hba1c"]
    out["ehr_duration_years"] = patient_row["diabetes_duration_years"]
    out["ehr_on_insulin"] = patient_row["on_insulin"]
    out["ehr_on_metformin"] = patient_row["on_metformin"]
    out["ehr_hypertension"] = patient_row["hypertension"]
    
    # H) Personal baseline - pers_
    pers_window = int(f_conf["personal_baseline_window_hours"] * 60 / interval) + 1
    pers_min_p = max(1, int(pers_window * min_frac))
    out["pers_glu_mean_24h"] = g.rolling(pers_window, min_periods=pers_min_p).mean()
    out["pers_glu_std_24h"] = g.rolling(pers_window, min_periods=pers_min_p).std()
    out["pers_glu_deviation"] = g - out["pers_glu_mean_24h"]
    out["pers_time_in_range_24h"] = g.between(70, 180).rolling(pers_window, min_periods=pers_min_p).mean()
    
    # I) Missingness - miss_
    out["miss_glucose_current"] = g.isna().astype(int)
    out["miss_glucose_frac_60m"] = g.isna().rolling(w60_steps, min_periods=1).mean()
    
    obs_mask = g.notna()
    obs_idxs = df.index[obs_mask]
    last_obs_idx = pd.Series(np.nan, index=df.index)
    last_obs_idx.loc[obs_idxs] = obs_idxs
    last_obs_idx = last_obs_idx.ffill()
    obs_mins = (df.index - last_obs_idx) * interval
    out["miss_min_since_last_obs"] = obs_mins.fillna(120).clip(upper=120)
    
    # ensure correct features
    expected_feats = get_feature_names()
    assert_no_forbidden(expected_feats)
    return out[["patient_id", "timestamp"] + expected_feats]

def build_features(wearable_df: pd.DataFrame, patients_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    dfs = []
    p_dict = {row["patient_id"]: row for _, row in patients_df.iterrows()}
    
    for pid, grp in wearable_df.groupby("patient_id"):
        feat_df = build_features_for_patient(grp, p_dict[pid], config)
        dfs.append(feat_df)
        
    return pd.concat(dfs, ignore_index=True)
