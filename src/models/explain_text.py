EXPLAIN_TEMPLATES = {
    "meal_cob_estimate": {
        "high": "Recent meal is still being absorbed (high carbs on board)",
        "low": "Little to no meal currently absorbing"
    },
    "meal_carbs_last_60m": {
        "high": "A large amount of carbs was consumed recently",
        "low": "No recent large meals"
    },
    "meal_min_since_last": {
        "high": "It has been a long time since the last meal",
        "low": "A meal was consumed very recently"
    },
    "glu_current": {
        "high": "Current glucose is already elevated",
        "low": "Current glucose is within safe bounds"
    },
    "glu_delta_30m": {
        "high": "Glucose has risen quickly in the last 30 minutes",
        "low": "Glucose is stable or falling over the last 30 minutes"
    },
    "glu_delta_60m": {
        "high": "Glucose has been rising over the past hour",
        "low": "Glucose is stable or falling over the last hour"
    },
    "glu_lag_15m": {
        "high": "Glucose was elevated 15 minutes ago",
        "low": "Glucose was low 15 minutes ago"
    },
    "pers_glu_deviation": {
        "high": "Glucose is deviating significantly from usual personal patterns",
        "low": "Glucose behavior is typical for this patient"
    },
    "sleep_is_asleep": {
        "high": "Patient is currently asleep (lowers risk naturally)",
        "low": "Patient is awake"
    },
    "sleep_state_awake": {
        "high": "Patient is awake",
        "low": "Patient is not fully awake"
    },
    "sleep_min_since_wake": {
        "high": "Patient has been awake for a while",
        "low": "Patient woke up recently, which can cause dawn phenomenon"
    },
    "hr_vs_personal_baseline": {
        "high": "Heart rate is elevated compared to personal norm (potential stress/activity)",
        "low": "Heart rate is calm"
    },
    "ehr_hba1c": {
        "high": "Patient has higher historical HbA1c (worse baseline control)",
        "low": "Patient has good historical HbA1c control"
    },
    "act_steps_last_60m": {
        "high": "Recent physical activity is helping to lower glucose risk",
        "low": "Sedentary recently"
    },
    "time_hour_sin": {
        "high": "Time of day correlates with higher metabolic risk",
        "low": "Time of day correlates with lower metabolic risk"
    }
}

def get_explanation_text(feature_name, value, is_high_value):
    if feature_name in EXPLAIN_TEMPLATES:
        return EXPLAIN_TEMPLATES[feature_name]["high" if is_high_value else "low"]
    
    return f"{feature_name} is {'high' if is_high_value else 'low'} ({value:.2f})"
