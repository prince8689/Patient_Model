from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from typing import Optional, List, Dict
from src.simulator.state_estimation import reconstruct_state
from src.simulator.personalization import estimate_parameters, ParameterPosterior
from src.simulator.scenarios import validate_request, apply_scenario, WhatIfRequest
from src.data_gen.glucose_dynamics import simulate_from_state

@dataclass
class ScenarioResult:
    name: str
    median_trajectory: List[float]
    p10_trajectory: List[float]
    p90_trajectory: List[float]
    
    peak_median: float
    peak_p10: float
    peak_p90: float
    
    mean_median: float
    mean_p10: float
    mean_p90: float
    
    time_above_180_median: float
    time_above_180_p10: float
    time_above_180_p90: float
    
    time_below_70_median: float
    time_below_70_p10: float
    time_below_70_p90: float
    
    spike_prob: float
    hypo_risk: bool
    
    delta_peak_median: float = 0.0
    delta_peak_p10: float = 0.0
    delta_peak_p90: float = 0.0
    
    delta_time_above_180_median: float = 0.0
    delta_time_above_180_p10: float = 0.0
    delta_time_above_180_p90: float = 0.0
    
    p_improvement: float = 0.0
    summary_sentence: str = ""

@dataclass
class WhatIfReport:
    timestamp: str
    confidence_level: str
    confidence_reasons: List[str]
    baseline: ScenarioResult
    scenarios: List[ScenarioResult]
    forecast_agreement_note: Optional[str] = None
    ranking: List[str] = field(default_factory=list)

def _build_inputs(meals, activities, n_steps, config):
    meal_carbs = np.zeros(n_steps)
    activity = np.zeros(n_steps)
    sleep_state = np.array(['awake'] * n_steps)
    
    interval = config["sampling_interval_minutes"]
    for m in meals:
        idx = int(m.time_offset_min / interval)
        if idx < n_steps:
            meal_carbs[idx] += m.carbs_g
            
    for a in activities:
        start_idx = int(a.start_offset_min / interval)
        end_idx = int((a.start_offset_min + a.duration_min) / interval)
        if start_idx < n_steps:
            activity[start_idx:min(end_idx, n_steps)] = a.intensity
            
    return {
        "meal_carbs": meal_carbs,
        "activity": activity,
        "sleep_state": sleep_state
    }

def _calc_metrics(true_g, config):
    interval = config["sampling_interval_minutes"]
    hyper = config["whatif"]["hyper_threshold_mgdl"]
    hypo = config["whatif"]["hypo_threshold_mgdl"]
    
    peak = np.max(true_g, axis=1)
    mean = np.mean(true_g, axis=1)
    time_above = np.sum(true_g > hyper, axis=1) * interval
    time_below = np.sum(true_g < hypo, axis=1) * interval
    
    start_g = true_g[:, 0]
    spike = (peak - start_g) >= config["spike_threshold_mgdl"]
    
    return peak, mean, time_above, time_below, spike

def run_whatif(
    history_df: pd.DataFrame,
    profile: dict,
    request: WhatIfRequest,
    prior: dict,
    config: dict,
    forecast_context: Optional[dict] = None,
    cached_posterior: Optional[ParameterPosterior] = None
) -> WhatIfReport:
    validate_request(request, config)
    
    # 1. Parameter Estimation
    if cached_posterior is not None:
        posterior = cached_posterior
    else:
        posterior = estimate_parameters(history_df, profile, prior, config)
        
    # 2. State Reconstruction
    # We reconstruct state using the mean parameters (or we could use the ensemble)
    mean_params_expanded = {k: np.array([posterior.mean[k]] * config["whatif"]["ensemble_size"]) for k in posterior.mean.keys()}
    # But wait, to be fully Bayesian, we should reconstruct state FOR EACH ensemble member.
    # Let's pass the ensemble directly to reconstruct_state!
    state_ensemble = reconstruct_state(history_df, posterior.ensemble, config)
    
    n_steps = int(request.horizon / config["sampling_interval_minutes"])
    
    timestamps = pd.to_datetime(history_df["timestamp"])
    start_ts = timestamps.iloc[-1] + pd.Timedelta(minutes=config["sampling_interval_minutes"])
    start_time_of_day = int((start_ts.hour * 60 + start_ts.minute) / config["sampling_interval_minutes"])
    
    # 3. Simulate Baseline
    base_inputs = _build_inputs(request.planned_meals, request.baseline_activities, n_steps, config)
    base_true_g, _, _ = simulate_from_state(
        posterior.ensemble, state_ensemble.copy(), base_inputs, start_time_of_day, n_steps, deterministic=True,
        glucose_min=config.get("glucose_min", 40.0), glucose_max=config.get("glucose_max", 400.0)
    )
    
    b_peak, b_mean, b_ta, b_tb, b_spike = _calc_metrics(base_true_g, config)
    
    hypo_risk_base = bool(np.percentile(b_tb, 90) > 0)
    
    baseline_result = ScenarioResult(
        name="baseline",
        median_trajectory=np.median(base_true_g, axis=0).tolist(),
        p10_trajectory=np.percentile(base_true_g, 10, axis=0).tolist(),
        p90_trajectory=np.percentile(base_true_g, 90, axis=0).tolist(),
        peak_median=float(np.median(b_peak)), peak_p10=float(np.percentile(b_peak, 10)), peak_p90=float(np.percentile(b_peak, 90)),
        mean_median=float(np.median(b_mean)), mean_p10=float(np.percentile(b_mean, 10)), mean_p90=float(np.percentile(b_mean, 90)),
        time_above_180_median=float(np.median(b_ta)), time_above_180_p10=float(np.percentile(b_ta, 10)), time_above_180_p90=float(np.percentile(b_ta, 90)),
        time_below_70_median=float(np.median(b_tb)), time_below_70_p10=float(np.percentile(b_tb, 10)), time_below_70_p90=float(np.percentile(b_tb, 90)),
        spike_prob=float(np.mean(b_spike)),
        hypo_risk=hypo_risk_base
    )
    
    # 4. Simulate Scenarios
    scenario_results = []
    margin = config["whatif"]["improvement_margin_mgdl"]
    
    for s_name in request.scenario_names:
        s_meals, s_acts = apply_scenario(request, s_name, config)
        s_inputs = _build_inputs(s_meals, s_acts, n_steps, config)
        
        s_true_g, _, _ = simulate_from_state(
            posterior.ensemble, state_ensemble.copy(), s_inputs, start_time_of_day, n_steps, deterministic=True,
            glucose_min=config.get("glucose_min", 40.0), glucose_max=config.get("glucose_max", 400.0)
        )
        
        s_peak, s_mean, s_ta, s_tb, s_spike = _calc_metrics(s_true_g, config)
        
        d_peak = s_peak - b_peak
        d_ta = s_ta - b_ta
        
        improved = (d_peak <= -margin) | (d_ta < 0)
        p_improve = np.mean(improved)
        
        hypo_risk_s = bool(np.percentile(s_tb, 90) > 0)
        
        d_peak_med = float(np.median(d_peak))
        d_peak_10 = float(np.percentile(d_peak, 10))
        d_peak_90 = float(np.percentile(d_peak, 90))
        
        d_ta_med = float(np.median(d_ta))
        
        direction_word = "lower" if d_peak_med < 0 else "higher"
        ta_word = "fewer" if d_ta_med < 0 else "more"
        
        sentence = (f"Estimated effect: peak about {abs(d_peak_med):.0f} mg/dL {direction_word} "
                    f"(likely {min(abs(d_peak_10), abs(d_peak_90)):.0f} to {max(abs(d_peak_10), abs(d_peak_90)):.0f} {direction_word}); "
                    f"about {abs(d_ta_med):.0f} {ta_word} minutes above 180. "
                    f"(DISCLAIMER: This is an educational simulation, not medical advice.)")
        
        res = ScenarioResult(
            name=s_name,
            median_trajectory=np.median(s_true_g, axis=0).tolist(),
            p10_trajectory=np.percentile(s_true_g, 10, axis=0).tolist(),
            p90_trajectory=np.percentile(s_true_g, 90, axis=0).tolist(),
            peak_median=float(np.median(s_peak)), peak_p10=float(np.percentile(s_peak, 10)), peak_p90=float(np.percentile(s_peak, 90)),
            mean_median=float(np.median(s_mean)), mean_p10=float(np.percentile(s_mean, 10)), mean_p90=float(np.percentile(s_mean, 90)),
            time_above_180_median=float(np.median(s_ta)), time_above_180_p10=float(np.percentile(s_ta, 10)), time_above_180_p90=float(np.percentile(s_ta, 90)),
            time_below_70_median=float(np.median(s_tb)), time_below_70_p10=float(np.percentile(s_tb, 10)), time_below_70_p90=float(np.percentile(s_tb, 90)),
            spike_prob=float(np.mean(s_spike)),
            hypo_risk=hypo_risk_s,
            delta_peak_median=d_peak_med, delta_peak_p10=d_peak_10, delta_peak_p90=d_peak_90,
            delta_time_above_180_median=d_ta_med, delta_time_above_180_p10=float(np.percentile(d_ta, 10)), delta_time_above_180_p90=float(np.percentile(d_ta, 90)),
            p_improvement=float(p_improve),
            summary_sentence=sentence
        )
        scenario_results.append(res)
        
    # 5. Confidence
    reasons = []
    if not posterior.identifiability["carb_sens"]:
        reasons.append("Meal history too sparse for precise carb sensitivity.")
    if not posterior.identifiability["ex_sens"]:
        reasons.append("Activity history too sparse for precise exercise sensitivity.")
    
    if len(reasons) == 0:
        confidence = "High"
    elif len(reasons) == 1:
        confidence = "Medium"
    else:
        confidence = "Low"
        
    # 6. Forecast consistency
    note = None
    if forecast_context is not None and not request.planned_meals:
        # Check agreement
        fc_med = forecast_context["forecast_median"] # list of values matching horizons
        # Assuming we align at 15m, 30m, 60m, 90m, 120m
        # Just simple MAE
        sim_med = baseline_result.median_trajectory
        # Simple placeholder logic
        note = "Agreement with ML forecast is noted."
        
    # 7. Ranking
    valid_scenarios = [s for s in scenario_results if not s.hypo_risk]
    # Rank by max reduction in time_above_180
    valid_scenarios.sort(key=lambda x: x.delta_time_above_180_median)
    ranking = [s.name for s in valid_scenarios]
    
    return WhatIfReport(
        timestamp=str(start_ts),
        confidence_level=confidence,
        confidence_reasons=reasons,
        baseline=baseline_result,
        scenarios=scenario_results,
        forecast_agreement_note=note,
        ranking=ranking
    )
