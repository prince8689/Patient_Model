import pandas as pd
from pathlib import Path
from src.twin.loader import load_frozen_artifacts
from src.features.engineering import build_features_for_patient
from src.utils.config import load_config
from src.twin.state import TwinState

def build_timeline(patient_id: str, start_time: str = None, end_time: str = None, config: dict = None) -> pd.DataFrame:
    if config is None:
        config = load_config()
        
    pipeline, calibrator, thresholds, meta = load_frozen_artifacts(config)
    
    raw_path = Path(config["paths"]["data_raw"]) / "wearable.csv"
    pat_path = Path(config["paths"]["data_raw"]) / "patients.csv"
    
    df = pd.read_csv(raw_path)
    df = df[df["patient_id"] == patient_id].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    pat_df = pd.read_csv(pat_path)
    pat_row = pat_df[pat_df["patient_id"] == patient_id].iloc[0]
    
    if start_time:
        df = df[df["timestamp"] >= pd.to_datetime(start_time)]
    if end_time:
        df = df[df["timestamp"] <= pd.to_datetime(end_time)]
        
    # Build batch features
    feat_df = build_features_for_patient(df, pat_row, config)
    
    # Predict
    features_list = pipeline.feature_names_in_
    X = feat_df[features_list]
    prob_raw = pipeline.predict_proba(X)[:, 1]
    
    if hasattr(calibrator, "transform"):
        import numpy as np
        prob_calib = np.clip(calibrator.transform(prob_raw), 0, 1)
    else:
        prob_calib = np.clip(calibrator.predict_proba(prob_raw.reshape(-1, 1))[:, 1], 0, 1)
        
    feat_df["probability"] = prob_calib
    
    t_med = thresholds["t_medium"]
    t_high = thresholds["t_high"]
    
    def assign_band(p):
        if p >= t_high: return "High"
        elif p >= t_med: return "Medium"
        return "Low"
        
    feat_df["band"] = feat_df["probability"].apply(assign_band)
    
    # Simulate alerts
    cooldown = config["twin"]["alert_cooldown_minutes"]
    last_alert = pd.to_datetime("2000-01-01")
    last_band = "Low"
    alerts = []
    
    for _, row in feat_df.iterrows():
        fire = False
        if row["band"] in ["Medium", "High"]:
            mins = (row["timestamp"] - last_alert).total_seconds() / 60.0
            if mins >= cooldown:
                fire = True
            elif row["band"] == "High" and last_band == "Medium":
                fire = True
                
        alerts.append(fire)
        if fire:
            last_alert = row["timestamp"]
        last_band = row["band"]
        
    feat_df["alert_fired"] = alerts
    
    out_cols = ["timestamp", "glu_current", "probability", "band", "alert_fired"]
    out_df = feat_df[out_cols].copy()
    
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
