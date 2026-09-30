import numpy as np

def generate_behaviors(
    n_days: int,
    archetype: str,
    meal_schedule_type: str,
    meal_ranges: dict,
    rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates meals, sleep, and activity arrays.
    """
    n_steps = n_days * 288
    meals = np.zeros(n_steps)
    sleep = np.full(n_steps, "awake", dtype=object)
    activity = np.zeros(n_steps, dtype=int)
    
    carb_mult = 1.15 if archetype == "poorly_controlled" else 1.0
    
    for d in range(n_days):
        day_offset = d * 288
        
        # MEALS
        if meal_schedule_type == "regular":
            b_mean, l_mean, d_mean, sd = 90, 156, 240, 4
        elif meal_schedule_type == "late_eater":
            b_mean, l_mean, d_mean, sd = 114, 180, 264, 4
        else: # irregular
            b_mean, l_mean, d_mean, sd = 96, 168, 252, 15
            
        b_time = int(np.clip(rng.normal(b_mean, sd), 0, 287))
        l_time = int(np.clip(rng.normal(l_mean, sd), 0, 287))
        d_time = int(np.clip(rng.normal(d_mean, sd), 0, 287))
        
        if meal_schedule_type != "irregular" or rng.uniform() > 0.2:
            meals[day_offset + b_time] = rng.uniform(*meal_ranges["breakfast"]) * carb_mult
        meals[day_offset + l_time] = rng.uniform(*meal_ranges["lunch"]) * carb_mult
        meals[day_offset + d_time] = rng.uniform(*meal_ranges["dinner"]) * carb_mult
        
        for _ in range(rng.integers(0, 3)):
            s_time = rng.integers(0, 288)
            meals[day_offset + s_time] += rng.uniform(*meal_ranges["snack"]) * carb_mult
            
        # SLEEP
        bed_time = int(rng.normal(282, 6)) % 288
        wake_time = int(rng.normal(84, 6)) % 288
        
        s_step = bed_time
        state = "light"
        while s_step != wake_time:
            idx = day_offset + s_step
            if idx < n_steps:
                sleep[idx] = state
            if rng.uniform() < 0.05:
                state = rng.choice(["light", "deep", "rem", "awake"], p=[0.4, 0.3, 0.2, 0.1])
            s_step = (s_step + 1) % 288
            
        # ACTIVITY
        act_prob = 0.15 if archetype == "poorly_controlled" else 0.3
        for _ in range(rng.integers(1, 4)):
            w_start = rng.integers(96, 240)
            w_len = rng.integers(2, 9)
            if day_offset + w_start + w_len <= n_steps:
                activity[day_offset + w_start : day_offset + w_start + w_len] = rng.integers(1, 3)
            
        if rng.uniform() < act_prob:
            wo_start = rng.integers(96, 240)
            wo_len = rng.integers(4, 10)
            if day_offset + wo_start + wo_len <= n_steps:
                activity[day_offset + wo_start : day_offset + wo_start + wo_len] = 3
            
    return meals, sleep, activity

def simulate_heart_rate(
    n_steps: int,
    base_hr: float,
    activity: np.ndarray,
    sleep: np.ndarray,
    rng: np.random.Generator
) -> np.ndarray:
    hr = np.zeros(n_steps)
    current_hr = base_hr
    for t in range(n_steps):
        target = base_hr
        if sleep[t] == "deep": target *= 0.85
        elif sleep[t] in ["light", "rem"]: target *= 0.90
        
        if activity[t] == 1: target += 15
        elif activity[t] == 2: target += 30
        elif activity[t] == 3: target += 55
        
        current_hr += 0.2 * (target - current_hr) + rng.normal(0, 1.5)
        hr[t] = current_hr
        
    return np.clip(hr + rng.normal(0, 2, n_steps), 40, 190)

def generate_steps(n_steps: int, activity: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    steps = np.zeros(n_steps, dtype=int)
    mask1 = activity == 1
    steps[mask1] = rng.integers(20, 60, size=np.sum(mask1))
    mask2 = activity == 2
    steps[mask2] = rng.integers(60, 100, size=np.sum(mask2))
    mask3 = activity == 3
    steps[mask3] = rng.integers(100, 160, size=np.sum(mask3))
    return steps
