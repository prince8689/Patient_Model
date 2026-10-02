
import numpy as np
import pandas as pd

from src.data_gen.glucose_dynamics import GlucoseState, simulate_from_state
from src.simulator.scenarios import apply_scenario
from src.simulator.whatif import WhatIfRequest, _build_inputs, _calc_metrics


def reproduce_true_counterfactual(
    patient_id: str,
    decision_time_min: int,
    request: WhatIfRequest,
    sim_params_df: pd.DataFrame,
    full_history_df: pd.DataFrame,
    config: dict,
    misspecified: bool = False
):
    """
    Runs the Oracle ground truth for a given decision time and what-if request.
    This uses the HIDDEN sim_params and the full future sequence to compute the exact
    true effect of the scenario under the generating data distribution.
    """
    row = sim_params_df[sim_params_df["patient_id"] == patient_id].iloc[0]
    
    params = {
        "baseline": np.array([row["fasting_glucose_baseline"]]),
        "dawn_amp": np.array([row["dawn_amplitude"]]),
        "carb_sens": np.array([row["carb_sensitivity"]]),
        "decay": np.array([row["glucose_decay_rate"]]),
        "ex_sens": np.array([row["exercise_sensitivity"]]),
        "sleep_quality": np.array([0.8]),
        "sensor_noise_sd": np.array([0.0])
    }
    
    if misspecified:
        params["ex_sens"] = params["ex_sens"] * 1.25 
        params["carb_sens"] = params["carb_sens"] * 0.75
        
    n_steps_history = int(decision_time_min / config["sampling_interval_minutes"])
    
    history_inputs = {
        "meal_carbs": full_history_df["meal_carbs_g"].fillna(0.0).values[:n_steps_history],
        "activity": full_history_df["activity_intensity"].fillna(0.0).values[:n_steps_history],
        "sleep_state": full_history_df["sleep_state"].fillna("awake").values[:n_steps_history]
    }
    
    initial_glucose = full_history_df["glucose_mgdl"].values[0]
    if np.isnan(initial_glucose):
        initial_glucose = 100.0
        
    state = GlucoseState(
        glucose=np.array([initial_glucose]),
        gut1=np.array([0.0]),
        gut2=np.array([0.0]),
        ex_linger=np.array([0.0]),
        physio_noise=np.array([0.0])
    )
    
    timestamps = pd.to_datetime(full_history_df["timestamp"])
    start_ts = timestamps.iloc[0]
    start_time_of_day = int((start_ts.hour * 60 + start_ts.minute) / config["sampling_interval_minutes"])
    
    _, _, final_state = simulate_from_state(
        params, state, history_inputs, start_time_of_day, n_steps_history, deterministic=True,
        glucose_min=config.get("glucose_min", 40.0), glucose_max=config.get("glucose_max", 400.0)
    )
    
    n_steps_horizon = int(request.horizon / config["sampling_interval_minutes"])
    start_time_horizon = (start_time_of_day + n_steps_history) % 288
    
    b_inputs = _build_inputs(request.planned_meals, request.baseline_activities, n_steps_horizon, config)
    base_true_g, _, _ = simulate_from_state(
        params, final_state.copy(), b_inputs, start_time_horizon, n_steps_horizon, deterministic=True,
        glucose_min=config.get("glucose_min", 40.0), glucose_max=config.get("glucose_max", 400.0)
    )
    b_peak, b_mean, b_ta, b_tb, b_spike = _calc_metrics(base_true_g, config)
    
    oracle_effects = {}
    
    for s_name in request.scenario_names:
        s_meals, s_acts = apply_scenario(request, s_name, config)
        s_inputs = _build_inputs(s_meals, s_acts, n_steps_horizon, config)
        
        s_true_g, _, _ = simulate_from_state(
            params, final_state.copy(), s_inputs, start_time_horizon, n_steps_horizon, deterministic=True,
            glucose_min=config.get("glucose_min", 40.0), glucose_max=config.get("glucose_max", 400.0)
        )
        s_peak, s_mean, s_ta, s_tb, s_spike = _calc_metrics(s_true_g, config)
        
        d_peak = s_peak[0] - b_peak[0]
        d_ta = s_ta[0] - b_ta[0]
        
        oracle_effects[s_name] = {
            "delta_peak": d_peak,
            "delta_time_above_180": d_ta,
            "delta_mean": s_mean[0] - b_mean[0]
        }
        
    return oracle_effects
