import pandas as pd
import pytest

from src.data_gen.patients import generate_patients
from src.data_gen.validate_patients import validate_patients
from src.utils.config import load_config


def test_generate_patients_schema():
    patients_df, sim_params_df = generate_patients(10, seed=42)
    assert len(patients_df) == 10
    assert len(sim_params_df) == 10
    
def test_reproducibility():
    p1, s1 = generate_patients(10, seed=42)
    p2, s2 = generate_patients(10, seed=42)
    p3, s3 = generate_patients(10, seed=43)
    pd.testing.assert_frame_equal(p1, p2)
    pd.testing.assert_frame_equal(s1, s2)
    
    with pytest.raises(AssertionError):
        pd.testing.assert_frame_equal(p1, p3)
        
def test_n_patients_respected():
    p1, _ = generate_patients(10, seed=42)
    assert len(p1) == 10
    p2, _ = generate_patients(40, seed=42)
    assert len(p2) == 40
        
def test_validation_passes():
    config = load_config()
    p, s = generate_patients(config["n_patients"], config["random_seed"])
    # Should not raise exception
    stats = validate_patients(p, s)
    assert stats["n_patients"] == config["n_patients"]
    
def test_validation_fails_corrupted():
    p, s = generate_patients(10, 42)
    # Corrupt BMI
    p.loc[0, "bmi"] = -5.0
    with pytest.raises(ValueError, match="BMI out of bounds"):
        validate_patients(p, s)
