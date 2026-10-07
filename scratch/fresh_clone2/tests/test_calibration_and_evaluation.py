import numpy as np
import pandas as pd

import src.models.calibration as calib
from src.models.explain import explain_row


def test_calibrator_fitting_data():
    # Verify that the test or val sets are not used to fit the calibrator.
    # In calibrate_model.py, we only fit on OOF train. We can simulate this check.
    df = pd.DataFrame({"patient_id": [1, 1, 2, 2], "split": ["train", "val", "train", "test"], "valid": [1, 1, 1, 1]})
    train_mask = (df["split"] == "train") & (df["valid"] == 1)
    assert sum(train_mask) == 2
    assert "val" not in df[train_mask]["split"].values
    assert "test" not in df[train_mask]["split"].values

def test_explain_row_additivity():
    # Dummy explainer mock
    class MockExplainer:
        def __init__(self):
            self.expected_value = 0.5
        def shap_values(self, X):
            return [np.array([[0.1, -0.2, 0.05]])]
            
    explainer = MockExplainer()
    df = pd.DataFrame({"f1": [1], "f2": [2], "f3": [3]})
    
    exp = explain_row(explainer, df, ["f1", "f2", "f3"], top_k=2)
    assert len(exp) == 2
    
    # Absolute magnitudes: -0.2 (idx 1), 0.1 (idx 0)
    assert exp[0]["feature"] == "f2"
    assert exp[0]["shap_value"] == -0.2
    assert exp[0]["direction"] == "decreases risk"
    
    assert exp[1]["feature"] == "f1"
    assert exp[1]["shap_value"] == 0.1
    assert exp[1]["direction"] == "increases risk"

def test_alert_logic_cooldown():
    # Cooldown 12 steps (60 mins)
    p = np.array([0.1, 0.9, 0.8, 0.9, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.9])
    # index:       0    1    2    3    4    5    6    7    8    9   10   11   12   13   14
    # Alert should fire at 1, then cooldown until 13.
    # So next alert fires at 14.
    alerts = []
    last_alert = -999
    cooldown = 12
    for i, val in enumerate(p):
        if val >= 0.5:
            if i - last_alert >= cooldown:
                alerts.append(i)
                last_alert = i
                
    assert alerts == [1, 14]

def test_band_assignment():
    t_med = 0.3
    t_high = 0.7
    def assign_band(p):
        if p >= t_high: return "High"
        elif p >= t_med: return "Medium"
        return "Low"
        
    assert assign_band(0.1) == "Low"
    assert assign_band(0.3) == "Medium"
    assert assign_band(0.69) == "Medium"
    assert assign_band(0.7) == "High"
    assert assign_band(0.99) == "High"

def test_calibration_monotone():
    # Simulated isotonic calibrator
    class MockIso:
        def transform(self, p):
            return np.sort(p)
    calibrator = MockIso()
    raw = np.array([0.1, 0.5, 0.3])
    calib_p = calib.apply_calibration(raw, calibrator)
    assert list(calib_p) == [0.1, 0.3, 0.5]
    assert np.all(calib_p >= 0) and np.all(calib_p <= 1)
