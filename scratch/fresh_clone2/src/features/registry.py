import pandas as pd

FEATURE_REGISTRY = [
    # A) Glucose
    {"name": "glu_current", "group": "A", "dtype": "float", "desc": "Current observed glucose", "units": "mg/dL"},
    {"name": "glu_lag_5m", "group": "A", "dtype": "float", "desc": "Glucose 5 min ago", "units": "mg/dL"},
    {"name": "glu_lag_15m", "group": "A", "dtype": "float", "desc": "Glucose 15 min ago", "units": "mg/dL"},
    {"name": "glu_lag_30m", "group": "A", "dtype": "float", "desc": "Glucose 30 min ago", "units": "mg/dL"},
    {"name": "glu_lag_60m", "group": "A", "dtype": "float", "desc": "Glucose 60 min ago", "units": "mg/dL"},
    {"name": "glu_lag_120m", "group": "A", "dtype": "float", "desc": "Glucose 120 min ago", "units": "mg/dL"},
    {"name": "glu_delta_5m", "group": "A", "dtype": "float", "desc": "Glucose change over 5 min", "units": "mg/dL"},
    {"name": "glu_delta_15m", "group": "A", "dtype": "float", "desc": "Glucose change over 15 min", "units": "mg/dL"},
    {"name": "glu_delta_30m", "group": "A", "dtype": "float", "desc": "Glucose change over 30 min", "units": "mg/dL"},
    {"name": "glu_delta_60m", "group": "A", "dtype": "float", "desc": "Glucose change over 60 min", "units": "mg/dL"},
    {"name": "glu_slope_30m", "group": "A", "dtype": "float", "desc": "Glucose slope over 30 min", "units": "mg/dL/min"},
    {"name": "glu_accel", "group": "A", "dtype": "float", "desc": "Glucose slope acceleration (15m - prev 15m)", "units": "mg/dL/min"},
    {"name": "glu_roll_mean_30m", "group": "A", "dtype": "float", "desc": "Rolling mean glucose 30 min", "units": "mg/dL"},
    {"name": "glu_roll_mean_60m", "group": "A", "dtype": "float", "desc": "Rolling mean glucose 60 min", "units": "mg/dL"},
    {"name": "glu_roll_mean_120m", "group": "A", "dtype": "float", "desc": "Rolling mean glucose 120 min", "units": "mg/dL"},
    {"name": "glu_roll_std_30m", "group": "A", "dtype": "float", "desc": "Rolling std glucose 30 min", "units": "mg/dL"},
    {"name": "glu_roll_std_60m", "group": "A", "dtype": "float", "desc": "Rolling std glucose 60 min", "units": "mg/dL"},
    {"name": "glu_roll_std_120m", "group": "A", "dtype": "float", "desc": "Rolling std glucose 120 min", "units": "mg/dL"},
    {"name": "glu_roll_min_30m", "group": "A", "dtype": "float", "desc": "Rolling min glucose 30 min", "units": "mg/dL"},
    {"name": "glu_roll_min_60m", "group": "A", "dtype": "float", "desc": "Rolling min glucose 60 min", "units": "mg/dL"},
    {"name": "glu_roll_min_120m", "group": "A", "dtype": "float", "desc": "Rolling min glucose 120 min", "units": "mg/dL"},
    {"name": "glu_roll_max_30m", "group": "A", "dtype": "float", "desc": "Rolling max glucose 30 min", "units": "mg/dL"},
    {"name": "glu_roll_max_60m", "group": "A", "dtype": "float", "desc": "Rolling max glucose 60 min", "units": "mg/dL"},
    {"name": "glu_roll_max_120m", "group": "A", "dtype": "float", "desc": "Rolling max glucose 120 min", "units": "mg/dL"},
    {"name": "glu_range_60m", "group": "A", "dtype": "float", "desc": "Glucose range (max-min) over 60 min", "units": "mg/dL"},
    {"name": "glu_above_180_frac_60m", "group": "A", "dtype": "float", "desc": "Fraction > 180 in 60m", "units": "ratio"},
    {"name": "glu_below_70_frac_60m", "group": "A", "dtype": "float", "desc": "Fraction < 70 in 60m", "units": "ratio"},
    
    # B) Meals
    {"name": "meal_carbs_last_60m", "group": "B", "dtype": "float", "desc": "Carbs eaten in last 60m", "units": "g"},
    {"name": "meal_carbs_last_120m", "group": "B", "dtype": "float", "desc": "Carbs eaten in last 120m", "units": "g"},
    {"name": "meal_carbs_last_240m", "group": "B", "dtype": "float", "desc": "Carbs eaten in last 240m", "units": "g"},
    {"name": "meal_min_since_last", "group": "B", "dtype": "float", "desc": "Minutes since last meal", "units": "min"},
    {"name": "meal_any_in_history", "group": "B", "dtype": "int", "desc": "Has any meal occurred in history", "units": "bool"},
    {"name": "meal_last_carbs_g", "group": "B", "dtype": "float", "desc": "Carbs of last meal", "units": "g"},
    {"name": "meal_count_last_6h", "group": "B", "dtype": "float", "desc": "Number of meals in last 6h", "units": "count"},
    {"name": "meal_cob_estimate", "group": "B", "dtype": "float", "desc": "Carbs on board estimate", "units": "g"},
    
    # C) Activity
    {"name": "act_steps_last_30m", "group": "C", "dtype": "float", "desc": "Steps in last 30m", "units": "count"},
    {"name": "act_steps_last_60m", "group": "C", "dtype": "float", "desc": "Steps in last 60m", "units": "count"},
    {"name": "act_steps_last_120m", "group": "C", "dtype": "float", "desc": "Steps in last 120m", "units": "count"},
    {"name": "act_max_intensity_last_60m", "group": "C", "dtype": "float", "desc": "Max activity intensity in last 60m", "units": "level"},
    {"name": "act_min_since_moderate", "group": "C", "dtype": "float", "desc": "Minutes since intensity >= 2", "units": "min"},
    {"name": "act_current_intensity", "group": "C", "dtype": "int", "desc": "Current activity intensity", "units": "level"},
    
    # D) Heart rate
    {"name": "hr_current", "group": "D", "dtype": "float", "desc": "Current heart rate", "units": "bpm"},
    {"name": "hr_roll_mean_30m", "group": "D", "dtype": "float", "desc": "Rolling mean HR 30m", "units": "bpm"},
    {"name": "hr_roll_mean_60m", "group": "D", "dtype": "float", "desc": "Rolling mean HR 60m", "units": "bpm"},
    {"name": "hr_roll_std_30m", "group": "D", "dtype": "float", "desc": "Rolling std HR 30m", "units": "bpm"},
    {"name": "hr_delta_30m", "group": "D", "dtype": "float", "desc": "HR change over 30m", "units": "bpm"},
    {"name": "hr_vs_personal_baseline", "group": "D", "dtype": "float", "desc": "HR vs rolling past 24h median", "units": "bpm"},
    
    # E) Sleep
    {"name": "sleep_is_asleep", "group": "E", "dtype": "int", "desc": "Currently asleep", "units": "bool"},
    {"name": "sleep_state_awake", "group": "E", "dtype": "int", "desc": "Sleep state: awake", "units": "bool"},
    {"name": "sleep_state_light", "group": "E", "dtype": "int", "desc": "Sleep state: light", "units": "bool"},
    {"name": "sleep_state_deep", "group": "E", "dtype": "int", "desc": "Sleep state: deep", "units": "bool"},
    {"name": "sleep_state_rem", "group": "E", "dtype": "int", "desc": "Sleep state: rem", "units": "bool"},
    {"name": "sleep_minutes_last_12h", "group": "E", "dtype": "float", "desc": "Minutes asleep in last 12h", "units": "min"},
    {"name": "sleep_deep_rem_frac_last_12h", "group": "E", "dtype": "float", "desc": "Fraction of sleep in deep/rem last 12h", "units": "ratio"},
    {"name": "sleep_min_since_wake", "group": "E", "dtype": "float", "desc": "Minutes since last wake transition", "units": "min"},
    
    # F) Time
    {"name": "time_hour_sin", "group": "F", "dtype": "float", "desc": "Hour of day sine", "units": "unitless"},
    {"name": "time_hour_cos", "group": "F", "dtype": "float", "desc": "Hour of day cosine", "units": "unitless"},
    {"name": "time_dow_sin", "group": "F", "dtype": "float", "desc": "Day of week sine", "units": "unitless"},
    {"name": "time_dow_cos", "group": "F", "dtype": "float", "desc": "Day of week cosine", "units": "unitless"},
    {"name": "time_is_weekend", "group": "F", "dtype": "int", "desc": "Is weekend", "units": "bool"},
    
    # G) EHR
    {"name": "ehr_age", "group": "G", "dtype": "float", "desc": "Age", "units": "years"},
    {"name": "ehr_sex_male", "group": "G", "dtype": "int", "desc": "Sex is male", "units": "bool"},
    {"name": "ehr_bmi", "group": "G", "dtype": "float", "desc": "BMI", "units": "kg/m2"},
    {"name": "ehr_hba1c", "group": "G", "dtype": "float", "desc": "HbA1c", "units": "%"},
    {"name": "ehr_duration_years", "group": "G", "dtype": "float", "desc": "Diabetes duration", "units": "years"},
    {"name": "ehr_on_insulin", "group": "G", "dtype": "int", "desc": "On insulin", "units": "bool"},
    {"name": "ehr_on_metformin", "group": "G", "dtype": "int", "desc": "On metformin", "units": "bool"},
    {"name": "ehr_hypertension", "group": "G", "dtype": "int", "desc": "Has hypertension", "units": "bool"},
    
    # H) Personal Baseline
    {"name": "pers_glu_mean_24h", "group": "H", "dtype": "float", "desc": "Past 24h mean glucose", "units": "mg/dL"},
    {"name": "pers_glu_std_24h", "group": "H", "dtype": "float", "desc": "Past 24h std glucose", "units": "mg/dL"},
    {"name": "pers_glu_deviation", "group": "H", "dtype": "float", "desc": "Current glucose minus past 24h mean", "units": "mg/dL"},
    {"name": "pers_time_in_range_24h", "group": "H", "dtype": "float", "desc": "Fraction 70-180 in past 24h", "units": "ratio"},
    
    # I) Missingness
    {"name": "miss_glucose_current", "group": "I", "dtype": "int", "desc": "Current glucose is missing", "units": "bool"},
    {"name": "miss_glucose_frac_60m", "group": "I", "dtype": "float", "desc": "Fraction missing in 60m", "units": "ratio"},
    {"name": "miss_min_since_last_obs", "group": "I", "dtype": "float", "desc": "Minutes since last observed glucose", "units": "min"}
]

FORBIDDEN_COLUMNS = {
    "spike_next_2h", "future_max_glucose", "valid", "split", "archetype",
    "baseline_insulin_sensitivity", "patient_id", "timestamp",
    "fasting_glucose_baseline", "dawn_amplitude", "carb_sensitivity", 
    "glucose_decay_rate", "exercise_sensitivity", "sleep_quality", 
    "sensor_noise_sd", "meal_schedule_type"
}

def get_feature_names():
    return [f["name"] for f in FEATURE_REGISTRY]

def assert_no_forbidden(feature_names):
    forbidden_found = [f for f in feature_names if f in FORBIDDEN_COLUMNS]
    if forbidden_found:
        raise ValueError(f"Forbidden features found: {forbidden_found}")
