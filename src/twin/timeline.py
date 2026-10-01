import pandas as pd
from pathlib import Path
from src.twin.loader import load_frozen_artifacts
from src.features.engineering import build_features_for_patient
from src.utils.config import load_config
from src.twin.state import TwinState
import numpy as np
import logging

def generate_timeline_for_patient(patient_id: str, config: dict, registry) -> pd.DataFrame:
    pipeline, calibrator, thresholds, meta = load_frozen_artifacts(config)
    
    raw_path = Path(config["paths"]["data_raw"]) / "wearable.csv"
    pat_path = Path(config["paths"]["data_raw"]) / "patients.csv"
    
    df = pd.read_csv(raw_path)
    df = df[df["patient_id"] == patient_id].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    pat_df = pd.read_csv(pat_path)
    pat_row = pat_df[pat_df["patient_id"] == patient_id].iloc[0]
    
    # Build batch features
    feat_df = build_features_for_patient(df, pat_row, config)
    
    # Predict
    features_list = pipeline.feature_names_in_
    X = feat_df[features_list]
    prob_raw = pipeline.predict_proba(X)[:, 1]
    
    if hasattr(calibrator, "transform"):
        prob_calib = np.clip(calibrator.transform(prob_raw), 0, 1)
    else:
        prob_calib = np.clip(calibrator.predict_proba(prob_raw.reshape(-1, 1))[:, 1], 0, 1)
        
    feat_df["risk_probability"] = prob_calib
    
    t_med = thresholds["t_medium"]
    t_high = thresholds["t_high"]
    
    def assign_band(p):
        if pd.isna(p): return "N/A"
        if p >= t_high: return "High"
        elif p >= t_med: return "Medium"
        return "Low"
        
    feat_df["risk_band"] = feat_df["risk_probability"].apply(assign_band)
    
    # Missingness and data_status
    feat_df["data_status"] = "ok"
    # first N hours warmup
    warmup_idx = 12 * config["twin"]["history_buffer_hours"]
    feat_df.loc[:warmup_idx, "data_status"] = "warming_up"
    feat_df.loc[feat_df["glu_current"].isna(), "data_status"] = "no_glucose"
    
    # Alert logic
    cooldown = config["twin"]["alert_cooldown_minutes"]
    last_alert = pd.to_datetime("2000-01-01")
    last_band = "Low"
    alert_bands = []
    
    for _, row in feat_df.iterrows():
        fire = False
        band = row["risk_band"]
        if row["data_status"] == "ok" and band in ["Medium", "High"]:
            mins = (row["timestamp"] - last_alert).total_seconds() / 60.0
            if mins >= cooldown:
                fire = True
            elif band == "High" and last_band == "Medium":
                fire = True
                
        if fire:
            alert_bands.append(band)
            last_alert = row["timestamp"]
        else:
            alert_bands.append(None)
        last_band = band
        
    feat_df["active_alert_band"] = alert_bands
    feat_df["active_alert_message"] = ["Risk alert" if x else None for x in alert_bands]
    
    # Other view columns
    feat_df["measurement_glucose_mgdl"] = feat_df["glu_current"]
    feat_df["measurement_meal_carbs_g"] = df["meal_carbs_g"]
    feat_df["measurement_activity_intensity"] = df["activity_intensity"]
    
    def get_trend(g1, g2):
        if pd.isna(g1) or pd.isna(g2): return "N/A"
        diff = g1 - g2
        if diff > 10: return "Rapidly Rising"
        elif diff > 2: return "Rising"
        elif diff < -10: return "Rapidly Falling"
        elif diff < -2: return "Falling"
        return "Stable"
        
    feat_df["glucose_trend_direction"] = [get_trend(feat_df["glu_current"].iloc[i], feat_df["glu_current"].iloc[i-3] if i>=3 else np.nan) for i in range(len(feat_df))]
    
    # TIR 24h
    window_288 = feat_df["glu_current"].rolling(288, min_periods=1)
    tir = window_288.apply(lambda x: 100 * ((x >= 70) & (x <= 180)).sum() / len(x.dropna()) if len(x.dropna())>0 else 0)
    feat_df["glucose_time_in_range_24h"] = tir
    
    # Minutes since meal
    last_meal = None
    mins_since = []
    for i, row in feat_df.iterrows():
        if row["measurement_meal_carbs_g"] > 0:
            last_meal = row["timestamp"]
        if last_meal:
            mins_since.append((row["timestamp"] - last_meal).total_seconds() / 60.0)
        else:
            mins_since.append(9999)
    feat_df["context_minutes_since_last_meal"] = mins_since
    
    # Zero out risk when not ok
    feat_df.loc[feat_df["data_status"] != "ok", "risk_probability"] = np.nan
    feat_df.loc[feat_df["data_status"] != "ok", "risk_band"] = "N/A"
    
    cols = [
        "timestamp", "data_status", "measurement_glucose_mgdl", 
        "measurement_meal_carbs_g", "measurement_activity_intensity",
        "glucose_trend_direction", "glucose_time_in_range_24h",
        "context_minutes_since_last_meal", "risk_probability", "risk_band",
        "active_alert_band", "active_alert_message"
    ]
    out_df = feat_df[cols].copy()
    
    out_dir = Path(config["paths"]["data_processed"]) / "twin_timelines"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(out_dir / f"{patient_id}.parquet")
    
    return out_df

def get_state_at(patient_id: str, timestamp: str, config: dict = None) -> TwinState:
    from src.twin.loader import TwinRegistry
    from src.twin.replay import StreamReplayer
    
    if config is None:
        config = load_config()
        
    ts = pd.to_datetime(timestamp)
    buf_hours = config["twin"]["history_buffer_hours"]
    start_ts = ts - pd.Timedelta(hours=buf_hours)
    
    replayer = StreamReplayer(Path(config["paths"]["data_raw"]) / "wearable.csv", patient_id, start_ts.isoformat(), ts.isoformat())
    registry = TwinRegistry(config)
    twin = registry.get(patient_id)
    
    state = None
    for sample in replayer.stream():
        state = twin.ingest(sample)
        
    return state

