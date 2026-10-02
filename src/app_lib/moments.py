import pandas as pd

from src.app_lib.data_access import get_config, get_patient_timeline


def available_moments(patient_id: str) -> list[pd.Timestamp]:
    timeline = get_patient_timeline(patient_id)
    # Filter out warm-up
    timeline["timestamp"] = pd.to_datetime(timeline["timestamp"])
    valid = timeline[timeline["data_status"] != "warming_up"]
    return sorted(valid["timestamp"].tolist())

def default_moment(patient_id: str, strategy: str = "most_interesting") -> pd.Timestamp:
    config = get_config()
    if config["app"].get("use_demo_bundle"):
        # For demo bundle, return the last available moment in timeline
        moms = available_moments(patient_id)
        if not moms:
            timeline = get_patient_timeline(patient_id)
            return pd.to_datetime(timeline["timestamp"].iloc[-1])
        return moms[-1]
        
    timeline = get_patient_timeline(patient_id)
    timeline["timestamp"] = pd.to_datetime(timeline["timestamp"])
    valid = timeline[timeline["data_status"] != "warming_up"].copy()
    
    if valid.empty:
        return timeline["timestamp"].iloc[-1]
        
    if strategy == "most_interesting":
        # Find moment with highest risk within a meal window
        # We define meal window as meal_min_since_last <= 120
        # Actually timeline has 'context_minutes_since_last_meal'
        if "context_minutes_since_last_meal" in valid.columns:
            meal_valid = valid[valid["context_minutes_since_last_meal"] <= 120]
            if not meal_valid.empty:
                max_risk_idx = meal_valid["risk_probability"].idxmax()
                return meal_valid.loc[max_risk_idx, "timestamp"]
                
        max_risk_idx = valid["risk_probability"].idxmax()
        return valid.loc[max_risk_idx, "timestamp"]
        
    return valid["timestamp"].iloc[-1]

def step_time(patient_id: str, current: pd.Timestamp, delta_minutes: int) -> pd.Timestamp:
    moms = available_moments(patient_id)
    if not moms:
        return current
    target = current + pd.Timedelta(minutes=delta_minutes)
    
    # closest moment
    closest = min(moms, key=lambda x: abs(x - target))
    return closest

def next_alert(patient_id: str, current: pd.Timestamp) -> pd.Timestamp:
    timeline = get_patient_timeline(patient_id)
    timeline["timestamp"] = pd.to_datetime(timeline["timestamp"])
    future_alerts = timeline[(timeline["timestamp"] > current) & (timeline["active_alert_band"].notna())]
    if future_alerts.empty:
        return current
    return future_alerts["timestamp"].iloc[0]

def previous_meal(patient_id: str, current: pd.Timestamp) -> pd.Timestamp:
    timeline = get_patient_timeline(patient_id)
    timeline["timestamp"] = pd.to_datetime(timeline["timestamp"])
    past_meals = timeline[(timeline["timestamp"] < current) & (timeline["measurement_meal_carbs_g"] > 0)]
    if past_meals.empty:
        return current
    return past_meals["timestamp"].iloc[-1]
