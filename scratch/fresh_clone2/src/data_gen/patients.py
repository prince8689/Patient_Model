
import numpy as np
import pandas as pd


def generate_patients(n_patients: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates synthetic patient profiles and hidden simulation parameters.
    
    Args:
        n_patients: Number of patients to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (patients_df, sim_params_df).
        patients_df is the EHR-like data.
        sim_params_df contains hidden parameters used for simulating wearable data
        and should NOT be used as ML features.
    """
    rng = np.random.default_rng(seed)
    
    # Archetype assignment
    archetypes = rng.choice(
        ["well_controlled", "moderate", "poorly_controlled"], 
        size=n_patients, 
        p=[0.35, 0.40, 0.25]
    )
    
    # Patient attributes
    patient_ids = [f"P{i:03d}" for i in range(1, n_patients + 1)]
    
    # Age: Normal(55, 10), clipped 30-78
    age = np.clip(rng.normal(55, 10, n_patients).astype(int), 30, 78)
    
    # Sex: 50/50
    sex = rng.choice(["M", "F"], size=n_patients)
    
    # BMI: Normal(29, 4.5), slightly higher for poorly controlled
    bmi_base = rng.normal(29, 4.5, n_patients)
    bmi_shift = np.where(archetypes == "poorly_controlled", rng.uniform(1.0, 3.0, n_patients), 0)
    bmi = np.clip(bmi_base + bmi_shift, 20.0, 42.0)
    
    # Diabetes duration
    # Gamma like, pos correlated with age, max age-25
    duration_mean = (age - 25) * 0.3
    duration_mean = np.clip(duration_mean, 0.5, 20)
    duration = np.clip(rng.gamma(shape=duration_mean, scale=1.0), 0.5, 25.0)
    duration = np.minimum(duration, age - 25.0)
    duration = np.maximum(duration, 0.5)
    
    # HbA1c
    hba1c_base = np.where(
        archetypes == "well_controlled", rng.normal(6.5, 0.5, n_patients),
        np.where(archetypes == "moderate", rng.normal(7.6, 0.6, n_patients),
                 rng.normal(9.0, 0.8, n_patients))
    )
    hba1c_duration_effect = (duration / 25.0) * 2.0
    hba1c_bmi_effect = ((bmi - 20) / 22.0) * 0.5
    hba1c = np.clip(hba1c_base + hba1c_duration_effect + hba1c_bmi_effect, 5.7, 12.5)
    
    # Metformin
    on_metformin = rng.binomial(1, 0.85, n_patients)
    
    # Insulin
    # Probability increases with duration and hba1c
    insulin_logit = -5.0 + 0.3 * hba1c + 0.1 * duration
    insulin_prob = 1 / (1 + np.exp(-insulin_logit))
    on_insulin = rng.binomial(1, insulin_prob)
    
    # Hypertension
    ht_logit = -4.0 + 0.05 * age + 0.1 * (bmi - 25)
    ht_prob = 1 / (1 + np.exp(-ht_logit))
    hypertension = rng.binomial(1, ht_prob)
    
    # Insulin sensitivity
    # 0.2 to 1.0, negative correlation with bmi, hba1c, duration
    ins_sens_base = 1.0 - 0.02 * (bmi - 20) - 0.05 * (hba1c - 5.7) - 0.01 * duration
    ins_sens_base += rng.normal(0, 0.1, n_patients)
    ins_sens_base = np.where(archetypes == "poorly_controlled", ins_sens_base - 0.2, ins_sens_base)
    baseline_insulin_sensitivity = np.clip(ins_sens_base, 0.2, 1.0)
    
    patients_df = pd.DataFrame({
        "patient_id": patient_ids,
        "age": age,
        "sex": sex,
        "bmi": np.round(bmi, 2),
        "hba1c": np.round(hba1c, 2),
        "diabetes_duration_years": np.round(duration, 1),
        "on_insulin": on_insulin,
        "on_metformin": on_metformin,
        "hypertension": hypertension,
        "baseline_insulin_sensitivity": np.round(baseline_insulin_sensitivity, 3)
    })
    
    # Simulation Parameters
    # fasting_glucose_baseline: ~28.7*hba1c - 46.7, fasting is 85-90% of that
    eag = 28.7 * hba1c - 46.7
    fasting_glucose = eag * rng.uniform(0.85, 0.90, n_patients) + rng.normal(0, 5, n_patients)
    fasting_glucose_baseline = np.round(np.clip(fasting_glucose, 70, 200), 1)
    
    # carb_sensitivity: 8-30, higher for poorer control
    carb_sens = np.where(
        archetypes == "well_controlled", rng.uniform(8, 15, n_patients),
        np.where(archetypes == "moderate", rng.uniform(12, 22, n_patients),
                 rng.uniform(18, 30, n_patients))
    )
    
    # glucose_decay_rate: 0.01-0.04, tied to insulin sensitivity
    decay = 0.01 + 0.03 * ((baseline_insulin_sensitivity - 0.2) / 0.8)
    decay += rng.normal(0, 0.002, n_patients)
    glucose_decay_rate = np.round(np.clip(decay, 0.01, 0.04), 4)
    
    dawn_amplitude = np.round(rng.uniform(0, 25, n_patients), 1)
    exercise_sensitivity = np.round(rng.uniform(0.5, 3.0, n_patients), 2)
    
    meal_schedules = rng.choice(["regular", "irregular", "late_eater"], size=n_patients)
    sleep_quality = np.round(rng.uniform(0.3, 1.0, n_patients), 2)
    sensor_noise_sd = np.round(rng.uniform(2.0, 6.0, n_patients), 2)
    
    sim_params_df = pd.DataFrame({
        "patient_id": patient_ids,
        "archetype": archetypes,
        "fasting_glucose_baseline": fasting_glucose_baseline,
        "carb_sensitivity": np.round(carb_sens, 2),
        "glucose_decay_rate": glucose_decay_rate,
        "dawn_amplitude": dawn_amplitude,
        "exercise_sensitivity": exercise_sensitivity,
        "meal_schedule_type": meal_schedules,
        "sleep_quality": sleep_quality,
        "sensor_noise_sd": sensor_noise_sd
    })
    
    return patients_df, sim_params_df
