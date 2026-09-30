import numpy as np
from sklearn.calibration import calibration_curve

def expected_calibration_error(y_true, y_prob, n_bins=10):
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy='quantile')
    return float(np.mean(np.abs(prob_true - prob_pred)))

def apply_calibration(prob, calibrator):
    """Applies a trained calibrator to raw probabilities. Returns probabilities bounded in [0, 1]."""
    # IsotonicRegression expects 1D array, CalibratedClassifierCV might expect 2D
    # It depends on what the calibrator is.
    
    # If using sklearn.calibration.CalibratedClassifierCV or similar, it usually takes X, 
    # but since we fit it directly on probabilities, we'll assume it's just a 1D or 2D mapping.
    
    # If it's an IsotonicRegression:
    if hasattr(calibrator, "transform"):
        p_calib = calibrator.transform(prob)
    # If it's a LogisticRegression (Platt scaling) on probabilities:
    elif hasattr(calibrator, "predict_proba"):
        p_calib = calibrator.predict_proba(prob.reshape(-1, 1))[:, 1]
    else:
        p_calib = calibrator.predict(prob) # fallback
        
    return np.clip(p_calib, 0, 1)

def predict_calibrated_proba(pipeline_model, calibrator, feature_df, feature_names):
    """
    Day 8 interface: predicts on the DataFrame, applying the calibrator.
    """
    X = feature_df[feature_names]
    prob_raw = pipeline_model.predict_proba(X)[:, 1]
    prob_calib = apply_calibration(prob_raw, calibrator)
    return prob_calib
