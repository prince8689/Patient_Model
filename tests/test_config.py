import pytest
from src.utils.config import load_config

def test_load_config():
    config = load_config()
    
    assert isinstance(config, dict)
    
    required_keys = [
        "random_seed",
        "n_patients",
        "days_per_patient",
        "sampling_interval_minutes",
        "spike_threshold_mgdl",
        "prediction_horizon_minutes",
        "lookback_window_minutes",
        "glucose_target_range",
        "paths"
    ]
    
    for key in required_keys:
        assert key in config, f"Missing required key: {key}"
        
    assert config["paths"]["data_raw"] == "data/raw"
