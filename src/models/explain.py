import numpy as np
import pandas as pd
import shap
from .explain_text import get_explanation_text

def explain_row(explainer, feature_row_df, feature_names, top_k=3):
    """
    Returns SHAP explanation for a single row.
    """
    X = feature_row_df[feature_names]
    shap_vals = explainer.shap_values(X)[0] # raw margin
    
    # Sort by absolute SHAP value
    indices = np.argsort(-np.abs(shap_vals))[:top_k]
    
    explanations = []
    for idx in indices:
        f_name = feature_names[idx]
        f_val = X[f_name].iloc[0]
        s_val = shap_vals[idx]
        
        # Simple heuristic for 'is_high_value': is it above feature mean?
        # Since we don't have global stats here, we just use a generic 'high' or 'low'
        # In a real system we'd compare to median.
        # Let's say if f_val > 0.5 (for normalized/boolean) or arbitrarily.
        # Actually, if s_val > 0 it's pushing risk UP. We use that to pick the text logic slightly
        
        # A simpler logic: the text tells the user what the model saw.
        direction = "increases risk" if s_val > 0 else "decreases risk"
        is_high = s_val > 0 # rough proxy, assumes monotonic.
        
        text = get_explanation_text(f_name, f_val, is_high)
        
        explanations.append({
            "feature": f_name,
            "feature_value": float(f_val) if not pd.isna(f_val) else None,
            "shap_value": float(s_val),
            "direction": direction,
            "human_readable": text
        })
        
    return explanations

def group_shap(shap_values_matrix, feature_names):
    """
    Groups SHAP absolute importance by prefix.
    """
    groups = {"glu": 0.0, "meal": 0.0, "act": 0.0, "hr": 0.0, "sleep": 0.0, "time": 0.0, "ehr": 0.0, "pers": 0.0, "miss": 0.0}
    
    abs_shap = np.abs(shap_values_matrix).mean(axis=0)
    
    for val, name in zip(abs_shap, feature_names):
        prefix = name.split("_")[0]
        if prefix in groups:
            groups[prefix] += val
            
    return groups
