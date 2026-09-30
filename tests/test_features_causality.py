import pytest
import numpy as np
import pandas as pd
from src.utils.config import load_config
from src.features.engineering import build_features_for_patient, build_features
from src.features.registry import assert_no_forbidden, get_feature_names, FORBIDDEN_COLUMNS

@pytest.fixture
def sample_patient_data():
    config = load_config()
    
    ts = pd.date_range("2026-01-01", periods=576, freq="5min")
    np.random.seed(42)
    df = pd.DataFrame({
        "patient_id": ["P1"] * 576,
        "timestamp": ts,
        "glucose_mgdl": 100 + np.random.randn(576).cumsum(),
        "meal_carbs_g": np.where(np.random.rand(576) > 0.98, 50, 0),
        "activity_intensity": np.random.choice([0, 1, 2, 3], size=576, p=[0.7, 0.1, 0.1, 0.1]),
        "steps": np.random.randint(0, 100, size=576),
        "heart_rate": 60 + np.random.randn(576) * 10,
        "sleep_state": np.where(ts.hour < 7, "deep", "awake")
    })
    
    row = pd.Series({
        "patient_id": "P1",
        "age": 55, "sex": "M", "bmi": 28.0, "hba1c": 7.5,
        "diabetes_duration_years": 5.0, "on_insulin": 0, "on_metformin": 1, "hypertension": 1
    })
    return df, row, config

def test_no_forbidden_in_registry():
    features = get_feature_names()
    assert_no_forbidden(features)
    for f in features:
        assert f not in FORBIDDEN_COLUMNS

def test_causality(sample_patient_data):
    df, row, config = sample_patient_data
    
    full_feats = build_features_for_patient(df, row, config)
    cut_idxs = [100, 250, 500]
    
    for cut_idx in cut_idxs:
        truncated_df = df.iloc[:cut_idx+1].copy()
        trunc_feats = build_features_for_patient(truncated_df, row, config)
        
        for col in get_feature_names():
            if col in full_feats.columns and col in trunc_feats.columns:
                full_vals = full_feats.iloc[:cut_idx+1][col].values
                trunc_vals = trunc_feats.iloc[:cut_idx+1][col].values
                np.testing.assert_allclose(full_vals, trunc_vals, equal_nan=True, err_msg=f"Causality violated for {col} at {cut_idx}")

def test_perturbation(sample_patient_data):
    df, row, config = sample_patient_data
    
    full_feats = build_features_for_patient(df, row, config)
    
    cut_idx = 300
    perturbed_df = df.copy()
    perturbed_df.loc[cut_idx+1:, "glucose_mgdl"] *= 5.0
    perturbed_df.loc[cut_idx+1:, "meal_carbs_g"] += 100
    
    pert_feats = build_features_for_patient(perturbed_df, row, config)
    
    for col in get_feature_names():
        if col in full_feats.columns:
            full_vals = full_feats.iloc[:cut_idx+1][col].values
            pert_vals = pert_feats.iloc[:cut_idx+1][col].values
            np.testing.assert_allclose(full_vals, pert_vals, equal_nan=True, err_msg=f"Perturbation causality violated for {col}")

def test_patient_isolation(sample_patient_data):
    df_p1, row_p1, config = sample_patient_data
    
    df_p2 = df_p1.copy()
    df_p2["patient_id"] = "P2"
    df_p2["glucose_mgdl"] = 500 # clearly different
    row_p2 = row_p1.copy()
    row_p2["patient_id"] = "P2"
    
    wearable_df = pd.concat([df_p1, df_p2], ignore_index=True)
    patients_df = pd.DataFrame([row_p1, row_p2])
    
    feats_both = build_features(wearable_df, patients_df, config)
    feats_p1_isolated = build_features_for_patient(df_p1, row_p1, config)
    
    feats_both_p1 = feats_both[feats_both["patient_id"] == "P1"].reset_index(drop=True)
    
    for col in get_feature_names():
        if col in feats_both_p1.columns and col in feats_p1_isolated.columns:
            np.testing.assert_allclose(feats_both_p1[col].values, feats_p1_isolated[col].values, equal_nan=True)

def test_handcrafted_features():
    config = load_config()
    
    ts = pd.date_range("2026-01-01", periods=10, freq="5min")
    df = pd.DataFrame({
        "patient_id": ["P1"] * 10,
        "timestamp": ts,
        "glucose_mgdl": [100, 105, 110, 115, 120, 125, 130, np.nan, 140, 145],
        "meal_carbs_g": [0, 50, 0, 0, 0, 0, 0, 0, 0, 0],
        "activity_intensity": [0]*10,
        "steps": [0]*10,
        "heart_rate": [60]*10,
        "sleep_state": ["awake"]*10
    })
    
    row = pd.Series({"patient_id": "P1", "age": 50, "sex": "M", "bmi": 25.0, "hba1c": 6.5, "diabetes_duration_years": 1.0, "on_insulin": 0, "on_metformin": 1, "hypertension": 0})
    
    feats = build_features_for_patient(df, row, config)
    
    np.testing.assert_allclose(feats.loc[6, "glu_slope_30m"], 1.0, atol=1e-5)
    assert feats.loc[1, "glu_lag_5m"] == 100
    assert feats.loc[1, "glu_delta_5m"] == 5
    
    assert feats.loc[0, "meal_min_since_last"] == 360
    assert feats.loc[1, "meal_min_since_last"] == 0
    assert feats.loc[2, "meal_min_since_last"] == 5
    
    assert feats.loc[1, "meal_cob_estimate"] > 0
    assert feats.loc[2, "meal_cob_estimate"] < feats.loc[1, "meal_cob_estimate"]
    
    assert feats.loc[7, "miss_glucose_current"] == 1
    assert feats.loc[7, "miss_min_since_last_obs"] == 5
    assert feats.loc[8, "miss_min_since_last_obs"] == 0
