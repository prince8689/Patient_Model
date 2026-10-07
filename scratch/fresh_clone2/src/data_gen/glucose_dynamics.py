from dataclasses import dataclass

import numpy as np


@dataclass
class GlucoseState:
    glucose: np.ndarray # shape (n_ensemble,)
    gut1: np.ndarray
    gut2: np.ndarray
    ex_linger: np.ndarray
    physio_noise: np.ndarray # shape (n_ensemble,)
    
    def copy(self):
        return GlucoseState(
            self.glucose.copy(),
            self.gut1.copy(),
            self.gut2.copy(),
            self.ex_linger.copy(),
            self.physio_noise.copy()
        )

def simulate_from_state(
    params: dict,
    state: GlucoseState,
    inputs_future: dict,
    start_time_of_day: int,
    n_steps: int,
    deterministic: bool = False,
    rng: np.random.Generator | None = None,
    glucose_min: float = 40.0,
    glucose_max: float = 400.0
) -> tuple[np.ndarray, np.ndarray, GlucoseState]:
    """
    Simulates glucose dynamics forward in time, vectorized over an ensemble.
    
    params contains arrays of shape (n_ensemble,):
    - baseline, dawn_amp, carb_sens, decay, ex_sens, sleep_quality, sensor_noise_sd
    
    inputs_future contains arrays of shape (n_steps,):
    - meal_carbs, activity, sleep_state
    
    Returns:
    - true_glucose: (n_ensemble, n_steps)
    - observed_glucose: (n_ensemble, n_steps)
    - final_state: GlucoseState
    """
    baseline = params["baseline"]
    dawn_amp = params["dawn_amp"]
    carb_sens = params["carb_sens"]
    decay = params["decay"]
    ex_sens = params["ex_sens"]
    sleep_quality = params.get("sleep_quality", np.ones_like(baseline) * 0.8)
    sensor_noise_sd = params.get("sensor_noise_sd", np.zeros_like(baseline))
    
    meal_carbs = inputs_future["meal_carbs"]
    activity = inputs_future["activity"]
    sleep_state = inputs_future["sleep_state"]
    is_sleeping = (sleep_state != 'awake')
    
    n_ensemble = baseline.shape[0]
    
    true_glucose = np.zeros((n_ensemble, n_steps))
    observed_glucose = np.zeros((n_ensemble, n_steps))
    
    G = state.glucose.copy()
    gut1 = state.gut1.copy()
    gut2 = state.gut2.copy()
    ex_linger = state.ex_linger.copy()
    physio_noise = state.physio_noise.copy()
    
    time_of_day = (start_time_of_day + np.arange(n_steps)) % 288
    time_bump = np.exp(-0.5 * ((time_of_day - 78) / 18)**2)
    dawn_effect = dawn_amp[:, None] * time_bump[None, :]
    
    sleep_baseline_mod = np.where(is_sleeping, -5.0 + (1.0 - sleep_quality[:, None]) * 10.0, 0.0)
    
    if not deterministic and rng is None:
        rng = np.random.default_rng()
        
    for t in range(n_steps):
        gut1 = gut1 + meal_carbs[t]
        gut1_to_gut2 = gut1 * 0.15
        gut1 = gut1 - gut1_to_gut2
        gut2 = gut2 + gut1_to_gut2
        gut2_to_blood = gut2 * 0.15
        gut2 = gut2 - gut2_to_blood
        
        meal_input = (carb_sens / 10.0) * gut2_to_blood
        
        act = activity[t]
        if act > 0:
            ex_linger = ex_linger + act * ex_sens * 0.2
        ex_linger = ex_linger * 0.95
        
        baseline_now = baseline + dawn_effect[:, t] + sleep_baseline_mod[:, t]
        
        reversion = -decay * (G - baseline_now)
        
        if deterministic:
            physio_noise = physio_noise * 0.9
        else:
            physio_noise = physio_noise * 0.9 + rng.normal(0, 0.5, size=n_ensemble)
            
        G = G + reversion + meal_input - ex_linger + physio_noise
        G = np.clip(G, glucose_min, glucose_max)
        
        true_glucose[:, t] = G
        if deterministic:
            observed_glucose[:, t] = G
        else:
            obs = G + rng.normal(0, sensor_noise_sd, size=n_ensemble)
            observed_glucose[:, t] = np.clip(obs, glucose_min, glucose_max)
            
    final_state = GlucoseState(G, gut1, gut2, ex_linger, physio_noise)
    return true_glucose, observed_glucose, final_state


def simulate_glucose(
    baseline: float,
    dawn_amp: float,
    carb_sens: float,
    decay: float,
    ex_sens: float,
    meal_carbs: np.ndarray,
    activity: np.ndarray,
    sleep_state: np.ndarray,
    sleep_quality: float,
    sensor_noise_sd: float,
    rng: np.random.Generator,
    initial_glucose: float = None,
    glucose_min: float = 40.0,
    glucose_max: float = 400.0
) -> tuple[np.ndarray, np.ndarray]:
    
    n_steps = len(meal_carbs)
    if initial_glucose is None:
        initial_glucose = baseline
        
    state = GlucoseState(
        glucose=np.array([initial_glucose]),
        gut1=np.array([0.0]),
        gut2=np.array([0.0]),
        ex_linger=np.array([0.0]),
        physio_noise=np.array([0.0])
    )
    
    params = {
        "baseline": np.array([baseline]),
        "dawn_amp": np.array([dawn_amp]),
        "carb_sens": np.array([carb_sens]),
        "decay": np.array([decay]),
        "ex_sens": np.array([ex_sens]),
        "sleep_quality": np.array([sleep_quality]),
        "sensor_noise_sd": np.array([sensor_noise_sd])
    }
    
    inputs_future = {
        "meal_carbs": meal_carbs,
        "activity": activity,
        "sleep_state": sleep_state
    }
    
    true_g, obs_g, _ = simulate_from_state(
        params=params,
        state=state,
        inputs_future=inputs_future,
        start_time_of_day=0,
        n_steps=n_steps,
        deterministic=False,
        rng=rng,
        glucose_min=glucose_min,
        glucose_max=glucose_max
    )
    
    # simulate_from_state uses size=1, so we take [0] to match original scalar-built arrays.
    return true_g[0], obs_g[0]
