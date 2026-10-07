from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .behaviors import generate_behaviors, generate_steps, simulate_heart_rate
from .glucose_dynamics import simulate_glucose


def generate_wearable(patients_df: pd.DataFrame, sim_params_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    n_days = config["days_per_patient"]
    start_date = datetime.strptime(config["start_date"], "%Y-%m-%d")
    
    timestamps = [start_date + timedelta(minutes=5 * i) for i in range(n_days * 288)]
    dfs = []
    
    for i, p_row in patients_df.iterrows():
        pid = p_row["patient_id"]
        s_row = sim_params_df[sim_params_df["patient_id"] == pid].iloc[0]
        
        p_num = int(pid.replace("P", ""))
        rng = np.random.default_rng([config["random_seed"], p_num])
        
        meals, sleep, activity = generate_behaviors(
            n_days=n_days,
            archetype=s_row["archetype"],
            meal_schedule_type=s_row["meal_schedule_type"],
            meal_ranges=config["meal_carbs_ranges"],
            rng=rng
        )
        
        base_hr = config["resting_hr_base"] + p_row["bmi"] * config["hr_bmi_effect"] + p_row["age"] * config["hr_age_effect"]
        hr = simulate_heart_rate(len(meals), base_hr, activity, sleep, rng)
        steps = generate_steps(len(meals), activity, rng)
        
        true_G, obs_G = simulate_glucose(
            baseline=s_row["fasting_glucose_baseline"],
            dawn_amp=s_row["dawn_amplitude"],
            carb_sens=s_row["carb_sensitivity"],
            decay=s_row["glucose_decay_rate"],
            ex_sens=s_row["exercise_sensitivity"],
            meal_carbs=meals,
            activity=activity,
            sleep_state=sleep,
            sleep_quality=s_row["sleep_quality"],
            sensor_noise_sd=s_row["sensor_noise_sd"],
            rng=rng,
            glucose_min=config["glucose_min"],
            glucose_max=config["glucose_max"]
        )
        
        mask = rng.uniform(0, 1, len(obs_G)) < config["missing_rate"]
        for d in range(n_days):
            if rng.uniform() < config["gap_probability_per_day"]:
                gap_start = d * 288 + rng.integers(0, 288 - 18)
                gap_len = rng.integers(6, 19)
                mask[gap_start : gap_start + gap_len] = True
                
        obs_G[mask] = np.nan
        
        p_df = pd.DataFrame({
            "patient_id": pid,
            "timestamp": [ts.isoformat() for ts in timestamps],
            "glucose_mgdl": np.round(obs_G, 1),
            "heart_rate": np.round(hr, 1),
            "steps": steps,
            "sleep_state": sleep,
            "meal_carbs_g": np.round(meals, 1),
            "activity_intensity": activity
        })
        dfs.append(p_df)
        
    return pd.concat(dfs, ignore_index=True)
