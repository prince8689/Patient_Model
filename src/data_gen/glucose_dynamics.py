import numpy as np

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
    """
    Simulates glucose dynamics over time using a discrete-time compartmental model.
    
    Update rules (per 5-minute step):
    1. Carb absorption: Two compartments (gut1 -> gut2 -> blood).
       meal_input = (carb_sens / 10) * absorbed_carbs.
    2. Mean reversion: G moves toward baseline_now at `decay` rate.
    3. baseline_now = baseline + dawn_effect (smooth bump 05:00-08:00).
    4. Exercise effect: activity reduces glucose, lingering effect.
    5. Sleep effect: lowers glucose slightly during sleep.
    6. Physiological noise: AR(1) autocorrelated noise.
    7. Sensor noise: Gaussian noise added to observed glucose.
    """
    n_steps = len(meal_carbs)
    true_glucose = np.zeros(n_steps)
    observed_glucose = np.zeros(n_steps)
    
    if initial_glucose is None:
        initial_glucose = baseline
        
    G = initial_glucose
    gut1 = 0.0
    gut2 = 0.0
    ex_linger = 0.0
    physio_noise = 0.0
    
    # Dawn effect
    time_of_day = np.arange(n_steps) % 288
    # bump centered around step 78 (06:30), width ~ 24 steps
    dawn_effect = dawn_amp * np.exp(-0.5 * ((time_of_day - 78) / 18)**2)
    
    # Sleep effect
    is_sleeping = (sleep_state != 'awake')
    sleep_baseline_mod = np.where(is_sleeping, -5.0 + (1.0 - sleep_quality) * 10.0, 0.0)
    
    for t in range(n_steps):
        # 1. Carb absorption
        gut1 += meal_carbs[t]
        gut1_to_gut2 = gut1 * 0.15
        gut1 -= gut1_to_gut2
        gut2 += gut1_to_gut2
        gut2_to_blood = gut2 * 0.15
        gut2 -= gut2_to_blood
        
        meal_input = (carb_sens / 10.0) * gut2_to_blood
        
        # 2. Exercise
        act = activity[t]
        if act > 0:
            ex_linger += act * ex_sens * 0.2
        ex_linger *= 0.95
        
        # 3. Baseline
        baseline_now = baseline + dawn_effect[t] + sleep_baseline_mod[t]
        
        # 4. Update G
        reversion = -decay * (G - baseline_now)
        
        # 5. Physiological noise
        physio_noise = 0.9 * physio_noise + rng.normal(0, 0.5)
        
        G = G + reversion + meal_input - ex_linger + physio_noise
        G = np.clip(G, glucose_min, glucose_max)
        
        true_glucose[t] = G
        observed_glucose[t] = np.clip(G + rng.normal(0, sensor_noise_sd), glucose_min, glucose_max)
        
    return true_glucose, observed_glucose
