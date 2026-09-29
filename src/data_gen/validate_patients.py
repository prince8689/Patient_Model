import pandas as pd
import numpy as np

def validate_patients(patients_df: pd.DataFrame, sim_params_df: pd.DataFrame) -> dict:
    """
    Validates the generated patient data against requirements.
    Raises ValueError if checks fail. Returns a dict of summary statistics.
    """
    # Schema checks
    req_patient_cols = [
        "patient_id", "age", "sex", "bmi", "hba1c", "diabetes_duration_years",
        "on_insulin", "on_metformin", "hypertension", "baseline_insulin_sensitivity"
    ]
    if list(patients_df.columns) != req_patient_cols:
        raise ValueError(f"patients_df columns do not match expected schema.\nExpected: {req_patient_cols}\nGot: {list(patients_df.columns)}")
        
    req_sim_cols = [
        "patient_id", "archetype", "fasting_glucose_baseline", "carb_sensitivity",
        "glucose_decay_rate", "dawn_amplitude", "exercise_sensitivity",
        "meal_schedule_type", "sleep_quality", "sensor_noise_sd"
    ]
    if list(sim_params_df.columns) != req_sim_cols:
        raise ValueError("sim_params_df columns do not match expected schema.")
        
    # Unique IDs and matching
    if not patients_df["patient_id"].is_unique:
        raise ValueError("patient_id in patients_df is not unique.")
    if not sim_params_df["patient_id"].is_unique:
        raise ValueError("patient_id in sim_params_df is not unique.")
    if not set(patients_df["patient_id"]) == set(sim_params_df["patient_id"]):
        raise ValueError("patient_id sets do not match between DataFrames.")
        
    # No missing values
    if patients_df.isnull().any().any():
        raise ValueError("Missing values in patients_df.")
    if sim_params_df.isnull().any().any():
        raise ValueError("Missing values in sim_params_df.")
        
    # Ranges
    if not patients_df["age"].between(30, 78).all():
        raise ValueError("Age out of bounds [30, 78].")
    if not patients_df["bmi"].between(20, 42).all():
        raise ValueError("BMI out of bounds [20, 42].")
    if not patients_df["hba1c"].between(5.7, 12.5).all():
        raise ValueError("HbA1c out of bounds [5.7, 12.5].")
    if not patients_df["diabetes_duration_years"].between(0.5, 25).all():
        raise ValueError("Diabetes duration out of bounds [0.5, 25].")
    if not patients_df["baseline_insulin_sensitivity"].between(0.2, 1.0).all():
        raise ValueError("Insulin sensitivity out of bounds [0.2, 1.0].")
        
    # Binary/Categories
    if not set(patients_df["sex"]).issubset({"M", "F"}):
        raise ValueError("Sex column contains invalid values.")
    for col in ["on_insulin", "on_metformin", "hypertension"]:
        if not set(patients_df[col]).issubset({0, 1}):
            raise ValueError(f"{col} contains invalid values (must be 0 or 1).")
            
    # Duration <= age - 25
    if (patients_df["diabetes_duration_years"] > patients_df["age"] - 25).any():
        raise ValueError("Duration exceeds age - 25.")
        
    # Correlations
    corr_hba1c_dur = patients_df["hba1c"].corr(patients_df["diabetes_duration_years"])
    corr_ins_bmi = patients_df["baseline_insulin_sensitivity"].corr(patients_df["bmi"])
    corr_ins_hba1c = patients_df["baseline_insulin_sensitivity"].corr(patients_df["hba1c"])
    
    if len(patients_df) >= 40:
        if corr_hba1c_dur <= 0:
            raise ValueError(f"corr(hba1c, duration) must be > 0, got {corr_hba1c_dur:.2f}")
        if corr_ins_bmi >= 0:
            raise ValueError(f"corr(ins_sens, bmi) must be < 0, got {corr_ins_bmi:.2f}")
        if corr_ins_hba1c >= 0:
            raise ValueError(f"corr(ins_sens, hba1c) must be < 0, got {corr_ins_hba1c:.2f}")
            
    # Archetype proportions
    arch_counts = sim_params_df["archetype"].value_counts(normalize=True)
    # allow +/- 0.25 tolerance for n=40
    for arch, target in [("well_controlled", 0.35), ("moderate", 0.40), ("poorly_controlled", 0.25)]:
        actual = arch_counts.get(arch, 0)
        if abs(actual - target) > 0.25:
            raise ValueError(f"Archetype {arch} proportion {actual:.2f} is too far from {target}.")
            
    return {
        "n_patients": len(patients_df),
        "mean_age": np.round(patients_df["age"].mean(), 1),
        "mean_bmi": np.round(patients_df["bmi"].mean(), 1),
        "mean_hba1c": np.round(patients_df["hba1c"].mean(), 2),
        "pct_insulin": np.round(patients_df["on_insulin"].mean() * 100, 1),
        "pct_metformin": np.round(patients_df["on_metformin"].mean() * 100, 1),
        "archetype_counts": sim_params_df["archetype"].value_counts().to_dict()
    }
