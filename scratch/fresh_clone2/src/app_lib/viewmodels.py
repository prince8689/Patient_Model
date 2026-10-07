import json

import numpy as np
import pandas as pd

from src.app_lib.data_access import (
    get_config,
    get_demo_patients,
    get_patient_timeline,
    get_patient_wearable,
    get_patients_df,
    get_registry,
)
from src.app_lib.moments import default_moment
from src.twin.state import TwinState


def patient_overview(as_of: pd.Timestamp = None) -> pd.DataFrame:
    pids = get_demo_patients()
    patients_df = get_patients_df()
    
    rows = []
    for pid in pids:
        prof = patients_df[patients_df["patient_id"] == pid].iloc[0]
        moment = as_of if as_of else default_moment(pid)
        
        timeline = get_patient_timeline(pid)
        timeline["timestamp"] = pd.to_datetime(timeline["timestamp"])
        past = timeline[timeline["timestamp"] <= moment]
        
        if past.empty:
            continue
            
        latest = past.iloc[-1]
        
        # sparkline
        past_6h = past[past["timestamp"] >= moment - pd.Timedelta(hours=6)]
        sparkline_vals = past_6h["measurement_glucose_mgdl"].tolist()
        
        # alerts in last 24h
        past_24h = past[past["timestamp"] >= moment - pd.Timedelta(hours=24)]
        alerts_24h = int(past_24h["active_alert_band"].notna().sum())
        
        row = {
            "patient_id": pid,
            "age": prof["age"],
            "sex": prof["sex"],
            "hba1c": prof["hba1c"],
            "diabetes_duration": prof["diabetes_duration_years"],
            "insulin_use": bool(prof["on_insulin"]),
            "current_glucose": latest["measurement_glucose_mgdl"],
            "trend_direction": latest["glucose_trend_direction"],
            "band": latest.get("risk_band", "N/A"),
            "probability": latest.get("risk_probability", np.nan),
            "tir_24h": latest.get("glucose_time_in_range_24h", np.nan),
            "alerts_24h": alerts_24h,
            "data_status": latest["data_status"],
            "last_update": latest["timestamp"].isoformat(),
            "sparkline": sparkline_vals
        }
        rows.append(row)
        
    return pd.DataFrame(rows)

def twin_view(patient_id: str, as_of: pd.Timestamp, include_actual_overlay: bool = False) -> dict:
    config = get_config()
    
    if config["app"].get("use_demo_bundle"):
        import json
        with open(f"demo_bundle/states/{patient_id}_{as_of.strftime('%Y%m%d_%H%M')}.json", "r") as f:
            state_dict = json.load(f)
        state = TwinState.from_dict(state_dict)
    else:
        registry = get_registry()
        twin = registry.get(patient_id)
        
        # Replay to as_of
        wearable = get_patient_wearable(patient_id)
        wearable = wearable[wearable["timestamp"] <= as_of].copy()
        
        # reset twin (fastest way is to just create a new buffer manually, but we can use engine natively)
        # Actually DiaTwin doesn't have a reset, so we recreate it
        from src.twin.engine import DiaTwin
        twin = DiaTwin(
            profile=twin.profile, 
            pipeline=twin.pipeline, 
            calibrator=twin.calibrator, 
            thresholds=twin.thresholds, 
            config=twin.config, 
            explainer=twin.explainer,
            forecast_artifacts=twin.forecast_artifacts,
            whatif_artifacts=twin.whatif_artifacts
        )
        
        # ingest batch
        # buffer only needs last history_buffer_hours
        cutoff = as_of - pd.Timedelta(hours=config["twin"]["history_buffer_hours"])
        hist_w = wearable[wearable["timestamp"] >= cutoff]
        
        if hist_w.empty:
            state = twin.get_state() # will fail if empty, but we must have some data
        else:
            samples = hist_w.to_dict(orient="records")
            # need to handle cumulatives (meal, etc.) from BEFORE cutoff!
            # so we must ingest from beginning or just use the last known values.
            # to be safe, ingest the last 500 samples (which covers the 36h buffer and warmup)
            samples = wearable.to_dict(orient="records")
            cutoff_samples = samples[-500:] if len(samples) > 500 else samples
            for s in cutoff_samples[:-1]:
                twin.ingest(s)
            state = twin.ingest(cutoff_samples[-1])

    # build view dict
    view = {}
    view["profile"] = state.profile.to_dict()
    view["timestamp"] = state.timestamp
    view["data_quality"] = state.data_quality.to_dict()
    view["context"] = state.context.to_dict()
    
    view["kpis"] = {
        "current_glucose": state.glucose_summary.current_glucose,
        "trend_direction": state.glucose_summary.trend_direction,
        "trend_30m": state.glucose_summary.trend_30m,
        "tir_24h": state.glucose_summary.time_in_range_24h,
        "band": state.risk.band if state.risk else "N/A",
        "probability": state.risk.probability_calibrated if state.risk else None,
        "predicted_peak": state.forecast.predicted_peak if state.forecast else None,
        "predicted_peak_minutes": state.forecast.predicted_peak_minutes if state.forecast else None,
        "hypo_risk": state.forecast.hypo_risk_flag if state.forecast else False,
        "hyper_risk": state.forecast.hyper_risk_flag if state.forecast else False,
    }
    
    view["drivers"] = []
    if state.risk and state.risk.drivers:
        for d in state.risk.drivers:
            # Map raw feature names to human readable
            name = d["feature"]
            desc = name
            if "act" in name: desc = "Recent Activity"
            elif "meal" in name: desc = "Recent Meal"
            elif "glu" in name: desc = "Glucose Trend"
            elif "sleep" in name: desc = "Sleep State"
            view["drivers"].append({
                "name": desc,
                "raw_name": name,
                "value": d.get("feature_value", 0.0),
                "contribution": d.get("shap_value", 0.0)
            })
            
    view["alerts_48h"] = []
    # Get from timeline
    timeline = get_patient_timeline(patient_id)
    timeline["timestamp"] = pd.to_datetime(timeline["timestamp"])
    past_48h = timeline[(timeline["timestamp"] <= as_of) & (timeline["timestamp"] >= as_of - pd.Timedelta(hours=48))]
    alerts = past_48h[past_48h["active_alert_band"].notna()]
    for _, row in alerts.iterrows():
        view["alerts_48h"].append({
            "timestamp": row["timestamp"].isoformat(),
            "band": row["active_alert_band"],
            "message": row["active_alert_message"]
        })
    view["alerts_48h"].reverse() # newest first
    
    # risk history 48h
    view["risk_history"] = {
        "timestamp": past_48h["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
        "probability": past_48h["risk_probability"].tolist(),
        "band": past_48h["risk_band"].tolist()
    }
    
    # glucose past 6h
    past_6h = past_48h[past_48h["timestamp"] >= as_of - pd.Timedelta(hours=6)]
    view["glucose_history"] = {
        "timestamp": past_6h["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
        "glucose": past_6h["measurement_glucose_mgdl"].tolist(),
        "meal_carbs": past_6h["measurement_meal_carbs_g"].tolist(),
        "activity": past_6h["measurement_activity_intensity"].tolist()
    }
    
    # forecast
    if state.forecast and state.forecast.status == "ok":
        view["forecast"] = state.forecast.trajectory_5min
        view["forecast_summary"] = state.forecast.summary
        view["agreement"] = state.forecast.agreement_with_risk_band
    else:
        view["forecast"] = None
        view["forecast_summary"] = "Forecast unavailable."
        view["agreement"] = None
        
    # actual overlay
    view["actual_overlay"] = None
    if include_actual_overlay:
        wearable = get_patient_wearable(patient_id)
        future = wearable[(wearable["timestamp"] > as_of) & (wearable["timestamp"] <= as_of + pd.Timedelta(hours=2))]
        if not future.empty:
            view["actual_overlay"] = {
                "timestamp": future["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
                "glucose": future["glucose_mgdl"].tolist()
            }
            
    return view

def export_state_json(patient_id: str, as_of: pd.Timestamp) -> str:
    config = get_config()
    if config["app"].get("use_demo_bundle"):
        with open(f"demo_bundle/states/{patient_id}_{as_of.strftime('%Y%m%d_%H%M')}.json", "r") as f:
            return f.read()
            
    registry = get_registry()
    twin = registry.get(patient_id)
    
    wearable = get_patient_wearable(patient_id)
    wearable = wearable[wearable["timestamp"] <= as_of]
    
    from src.twin.engine import DiaTwin
    twin2 = DiaTwin(
        profile=twin.profile, 
        pipeline=twin.pipeline, 
        calibrator=twin.calibrator, 
        thresholds=twin.thresholds, 
        config=twin.config, 
        explainer=None,
        forecast_artifacts=None,
        whatif_artifacts=None
    )
    # We only need enough history to satisfy the history buffer (36 hours = 432 samples)
    samples = wearable.to_dict(orient="records")
    cutoff_samples = samples[-500:] if len(samples) > 500 else samples
    
    # Fast forward loop without full feature generation
    for s in cutoff_samples[:-1]:
        row = twin2._validate_sample(s)
        twin2.buffer.append(row)
        twin2.last_timestamp = row["timestamp"]
        twin2._update_cumulative_state(row)
        
        # Trim buffer
        cutoff = row["timestamp"] - pd.Timedelta(minutes=twin2.history_buffer_m)
        twin2.buffer = [r for r in twin2.buffer if r["timestamp"] >= cutoff]
        
    twin2.explainer = twin.explainer
    twin2.forecast_artifacts = twin.forecast_artifacts
    twin2.whatif_artifacts = twin.whatif_artifacts
    
    state = twin2.ingest(cutoff_samples[-1])
    return json.dumps(state.to_dict(), indent=2)
