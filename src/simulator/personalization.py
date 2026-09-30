import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from dataclasses import dataclass
from src.data_gen.glucose_dynamics import simulate_from_state, GlucoseState

@dataclass
class ParameterPosterior:
    mean: dict
    cov: np.ndarray
    ensemble: dict
    identifiability: dict
    effective_data_points: int

def get_param_bounds(config):
    return {
        "baseline": (60.0, 200.0),
        "dawn_amp": (0.0, 50.0),
        "carb_sens": (0.5, 4.0),
        "decay": (0.01, 0.2),
        "ex_sens": (0.0, 4.0)
    }

def objective_fn(
    x, param_names, history_df, config, prior_mean, prior_cov_inv, glucose_min, glucose_max
):
    n_steps = len(history_df)
    
    params = {name: np.array([val]) for name, val in zip(param_names, x)}
    params["sleep_quality"] = np.array([0.8])
    params["sensor_noise_sd"] = np.array([0.0])
    
    meal_carbs = history_df.get("meal_carbs_g", np.zeros(n_steps))
    if hasattr(meal_carbs, "values"): meal_carbs = meal_carbs.fillna(0.0).values
    activity = history_df.get("activity_intensity", np.zeros(n_steps))
    if hasattr(activity, "values"): activity = activity.fillna(0.0).values
    sleep_state = history_df.get("sleep_state", np.array(['awake']*n_steps))
    if hasattr(sleep_state, "values"): sleep_state = sleep_state.values
    sleep_state = np.where(pd.isna(sleep_state), 'awake', sleep_state)
    
    obs_glucose = history_df["glucose_mgdl"].values
    
    first_obs_idx = np.where(~np.isnan(obs_glucose))[0]
    initial_glucose = obs_glucose[first_obs_idx[0]] if len(first_obs_idx) > 0 else 100.0
    
    state = GlucoseState(
        glucose=np.array([initial_glucose]),
        gut1=np.array([0.0]),
        gut2=np.array([0.0]),
        ex_linger=np.array([0.0]),
        physio_noise=np.array([0.0])
    )
    
    inputs_future = {
        "meal_carbs": meal_carbs,
        "activity": activity,
        "sleep_state": sleep_state
    }
    
    timestamps = pd.to_datetime(history_df["timestamp"])
    first_ts = timestamps.iloc[0]
    start_time_of_day = int((first_ts.hour * 60 + first_ts.minute) / config["sampling_interval_minutes"])
    
    _, sim_obs, _ = simulate_from_state(
        params=params,
        state=state,
        inputs_future=inputs_future,
        start_time_of_day=start_time_of_day,
        n_steps=n_steps,
        deterministic=True,
        rng=None,
        glucose_min=glucose_min,
        glucose_max=glucose_max
    )
    sim_obs = sim_obs[0]
    
    valid_idx = ~np.isnan(obs_glucose)
    obs_residuals = sim_obs[valid_idx] - obs_glucose[valid_idx]
    
    if prior_mean is not None and prior_cov_inv is not None:
        diff = x - prior_mean
        try:
            L = np.linalg.cholesky(prior_cov_inv)
            prior_residuals = L.T @ diff
        except np.linalg.LinAlgError:
            prior_residuals = diff * np.sqrt(np.diag(prior_cov_inv))
    else:
        prior_residuals = np.zeros(len(x))
        
    return np.concatenate([obs_residuals, prior_residuals])

def estimate_parameters(history_df: pd.DataFrame, profile: dict, prior: dict, config: dict) -> ParameterPosterior:
    window_days = config["whatif"]["param_window_days"]
    lookback_points = int(window_days * 24 * 60 / config["sampling_interval_minutes"])
    fit_df = history_df.tail(lookback_points).copy()
    
    bounds_dict = get_param_bounds(config)
    param_names = ["baseline", "dawn_amp", "carb_sens", "decay", "ex_sens"]
    
    meal_carbs = fit_df.get("meal_carbs_g", pd.Series())
    activity = fit_df.get("activity_intensity", pd.Series())
    meal_episodes = (meal_carbs.fillna(0) > 0).sum()
    activity_episodes = (activity.fillna(0) > 0).sum()
    
    min_meal = config["whatif"]["min_meal_episodes"]
    min_ex = config["whatif"]["min_exercise_episodes"]
    
    identifiability = {
        "baseline": True,
        "dawn_amp": True,
        "decay": True,
        "carb_sens": bool(meal_episodes >= min_meal),
        "ex_sens": bool(activity_episodes >= min_ex)
    }
    
    prior_mean = prior.get("mean", None)
    prior_cov = prior.get("cov", None)
    
    x0 = []
    lb = []
    ub = []
    for p in param_names:
        lb.append(bounds_dict[p][0])
        ub.append(bounds_dict[p][1])
        if prior_mean is not None:
            x0.append(np.clip(prior_mean[p], bounds_dict[p][0], bounds_dict[p][1]))
        else:
            x0.append(np.mean(bounds_dict[p]))
            
    x0 = np.array(x0)
    lb = np.array(lb)
    ub = np.array(ub)
    
    prior_cov_inv = None
    if prior_cov is not None:
        prior_mean_arr = np.array([prior_mean[p] for p in param_names])
        prior_strength = config["whatif"]["prior_strength"]
        prior_cov_mat = np.array(prior_cov) / prior_strength
        for i, p in enumerate(param_names):
            if not identifiability[p]:
                prior_cov_mat[i, i] *= 0.01 
                
        prior_cov_inv = np.linalg.inv(prior_cov_mat)
    else:
        prior_mean_arr = None

    glucose_min = config.get("glucose_min", 40.0)
    glucose_max = config.get("glucose_max", 400.0)
    
    res = least_squares(
        objective_fn,
        x0,
        bounds=(lb, ub),
        args=(param_names, fit_df, config, prior_mean_arr, prior_cov_inv, glucose_min, glucose_max),
        method='trf',
        max_nfev=100
    )
    
    map_estimate = res.x
    
    J = res.jac
    H = J.T @ J
    
    try:
        post_cov = np.linalg.inv(H)
    except np.linalg.LinAlgError:
        post_cov = np.eye(len(map_estimate)) * 1e-4
        
    if prior_cov is not None:
        for i, p in enumerate(param_names):
            if not identifiability[p]:
                post_cov[i, :] = prior_cov_mat[i, :]
                post_cov[:, i] = prior_cov_mat[:, i]
                
    inflation = config["whatif"]["interval_inflation"]
    post_cov = post_cov * inflation
    
    # Ensure symmetry and positive semi-definiteness
    post_cov = (post_cov + post_cov.T) / 2
    eigvals, eigvecs = np.linalg.eigh(post_cov)
    eigvals = np.clip(eigvals, a_min=1e-8, a_max=None)
    post_cov = eigvecs @ np.diag(eigvals) @ eigvecs.T
    
    n_ensemble = config["whatif"]["ensemble_size"]
    rng = np.random.default_rng(config["random_seed"])
    
    ensemble_samples = rng.multivariate_normal(map_estimate, post_cov, size=n_ensemble)
    
    ensemble = {}
    mean_dict = {}
    for i, p in enumerate(param_names):
        ensemble_samples[:, i] = np.clip(ensemble_samples[:, i], bounds_dict[p][0], bounds_dict[p][1])
        ensemble[p] = ensemble_samples[:, i]
        mean_dict[p] = float(map_estimate[i])
        
    valid_obs = int((~np.isnan(fit_df["glucose_mgdl"].values)).sum())
        
    return ParameterPosterior(
        mean=mean_dict,
        cov=post_cov,
        ensemble=ensemble,
        identifiability=identifiability,
        effective_data_points=valid_obs
    )
