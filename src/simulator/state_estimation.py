import numpy as np
import pandas as pd
from src.data_gen.glucose_dynamics import GlucoseState

def reconstruct_state(history_df: pd.DataFrame, params: dict, config: dict) -> GlucoseState:
    """
    Reconstructs the internal state (GlucoseState) of a patient from their recent history,
    using a deterministic observer with correction gain.
    
    This is state estimation from noisy, partial data. Gut compartments are inferred
    from meal records, not measured.
    """
    n_ensemble = params["baseline"].shape[0]
    gain = config["whatif"]["observer_gain"]
    
    # We replay the last 8 hours, or the full history if less.
    lookback_points = int(8 * 60 / config["sampling_interval_minutes"])
    replay_df = history_df.tail(lookback_points).copy()
    
    # Extract inputs
    meal_carbs = replay_df.get("meal_carbs_g", np.zeros(len(replay_df)))
    if hasattr(meal_carbs, "values"):
        meal_carbs = meal_carbs.fillna(0.0).values
        
    activity = replay_df.get("activity_intensity", np.zeros(len(replay_df)))
    if hasattr(activity, "values"):
        activity = activity.fillna(0.0).values
        
    sleep_state = replay_df.get("sleep_state", np.array(['awake']*len(replay_df)))
    if hasattr(sleep_state, "values"):
        sleep_state = sleep_state.values
    sleep_state = np.where(pd.isna(sleep_state), 'awake', sleep_state)
    
    obs_glucose = replay_df["glucose_mgdl"].values
    
    # Initialization
    first_obs_idx = np.where(~np.isnan(obs_glucose))[0]
    initial_glucose = obs_glucose[first_obs_idx[0]] if len(first_obs_idx) > 0 else 100.0
    
    state = GlucoseState(
        glucose=np.ones(n_ensemble) * initial_glucose,
        gut1=np.zeros(n_ensemble),
        gut2=np.zeros(n_ensemble),
        ex_linger=np.zeros(n_ensemble),
        physio_noise=np.zeros(n_ensemble)
    )
    
    baseline = params["baseline"]
    dawn_amp = params["dawn_amp"]
    carb_sens = params["carb_sens"]
    decay = params["decay"]
    ex_sens = params["ex_sens"]
    sleep_quality = params.get("sleep_quality", np.ones_like(baseline) * 0.8)
    
    timestamps = pd.to_datetime(replay_df["timestamp"])
    first_ts = timestamps.iloc[0]
    start_time_of_day = int((first_ts.hour * 60 + first_ts.minute) / config["sampling_interval_minutes"])
    time_of_day_arr = (start_time_of_day + np.arange(len(replay_df))) % 288
    
    time_bump = np.exp(-0.5 * ((time_of_day_arr - 78) / 18)**2)
    dawn_effect = dawn_amp[:, None] * time_bump[None, :]
    
    is_sleeping = (sleep_state != 'awake')
    sleep_baseline_mod = np.where(is_sleeping, -5.0 + (1.0 - sleep_quality[:, None]) * 10.0, 0.0)
    
    glucose_min = config.get("glucose_min", 40.0)
    glucose_max = config.get("glucose_max", 400.0)
    
    for t in range(len(replay_df)):
        state.gut1 = state.gut1 + meal_carbs[t]
        gut1_to_gut2 = state.gut1 * 0.15
        state.gut1 = state.gut1 - gut1_to_gut2
        state.gut2 = state.gut2 + gut1_to_gut2
        gut2_to_blood = state.gut2 * 0.15
        state.gut2 = state.gut2 - gut2_to_blood
        
        meal_input = (carb_sens / 10.0) * gut2_to_blood
        
        act = activity[t]
        if act > 0:
            state.ex_linger = state.ex_linger + act * ex_sens * 0.2
        state.ex_linger = state.ex_linger * 0.95
        
        baseline_now = baseline + dawn_effect[:, t] + sleep_baseline_mod[:, t]
        
        reversion = -decay * (state.glucose - baseline_now)
        state.physio_noise = state.physio_noise * 0.9
        
        state.glucose = state.glucose + reversion + meal_input - state.ex_linger + state.physio_noise
        state.glucose = np.clip(state.glucose, glucose_min, glucose_max)
        
        y = obs_glucose[t]
        if not np.isnan(y):
            correction = gain * (y - state.glucose)
            state.glucose = state.glucose + correction
            state.physio_noise = state.physio_noise + (correction * 0.5)
            
    return state
