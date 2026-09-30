import pytest
import pandas as pd
import numpy as np
from src.data_gen.wearable import generate_wearable
from src.data_gen.glucose_dynamics import simulate_glucose
from src.data_gen.validate_wearable import validate_wearable
from src.utils.config import load_config
from src.data_gen.patients import generate_patients

def test_glucose_dynamics():
    rng = np.random.default_rng(42)
    n_steps = 100
    meals = np.zeros(n_steps)
    activity = np.zeros(n_steps, dtype=int)
    sleep = np.full(n_steps, "awake")
    
    # Test 1: Zero meals, stays near baseline
    true_g, obs_g = simulate_glucose(100, 0, 15, 0.02, 1.0, meals, activity, sleep, 1.0, 2.0, rng)
    assert np.abs(true_g.mean() - 100) < 10
    
    # Test 2: Large meal
    meals[10] = 50
    true_g2, _ = simulate_glucose(100, 0, 15, 0.02, 1.0, meals, activity, sleep, 1.0, 2.0, rng)
    assert true_g2.max() > true_g.max() + 20
    
    # Test 3: Exercise lowers peak
    activity[12:20] = 3
    true_g3, _ = simulate_glucose(100, 0, 15, 0.02, 1.0, meals, activity, sleep, 1.0, 2.0, rng)
    assert true_g3.max() < true_g2.max()

def test_wearable_reproducibility():
    config = load_config()
    config["days_per_patient"] = 2
    p1, s1 = generate_patients(3, 42)
    w1 = generate_wearable(p1, s1, config)
    w2 = generate_wearable(p1, s1, config)
    pd.testing.assert_frame_equal(w1, w2)

def test_wearable_independence():
    config = load_config()
    config["days_per_patient"] = 2
    p3, s3 = generate_patients(3, 42)
    w3 = generate_wearable(p3, s3, config)
    
    p2 = p3.iloc[:2].reset_index(drop=True)
    s2 = s3.iloc[:2].reset_index(drop=True)
    w2 = generate_wearable(p2, s2, config)
    
    w3_p2 = w3[w3["patient_id"].isin(p2["patient_id"])].reset_index(drop=True)
    pd.testing.assert_frame_equal(w3_p2, w2)
    
def test_validation_corrupted():
    config = load_config()
    config["days_per_patient"] = 2
    p, s = generate_patients(2, 42)
    w = generate_wearable(p, s, config)
    
    w.loc[0, "glucose_mgdl"] = -100
    with pytest.raises(ValueError, match="out of bounds"):
        validate_wearable(w, p, s)
