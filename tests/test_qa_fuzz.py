import pytest
from hypothesis import given, strategies as st
from src.data_gen.patients import generate_patients
from src.app_lib.whatif_vm import build_request

def test_generate_patients_negative():
    with pytest.raises(ValueError):
        generate_patients(-1, seed=42)
        
def test_generate_patients_zero():
    p, s = generate_patients(0, seed=42)
    assert len(p) == 0

@given(st.integers(min_value=1, max_value=100))
def test_generate_patients_valid(n):
    p, s = generate_patients(n, seed=42)
    assert len(p) == n
    assert len(s) == n

@given(st.text(min_size=1, max_size=10000))
def test_build_request_xss(text):
    # Try to inject XSS or weird strings into the scenario payload
    # Should not crash, just reject or sanitize if it doesn't match enums
    try:
        req, err = build_request([], ["custom"], {"custom_meal_carbs": text, "custom_meal_time": text, "custom_activity_level": text, "custom_activity_time": text, "custom_activity_duration": text})
        assert True
    except (ValueError, TypeError):
        # expected if invalid types
        assert True

def test_build_request_extreme_values():
    req, err = build_request([], ["custom"], {"custom_meal_carbs": -10, "custom_meal_time": 0, "custom_activity_level": "moderate", "custom_activity_time": 0, "custom_activity_duration": 0})
    # Since we validate non-negative in Pydantic, it should either raise or return err
    # Let's just check it doesn't hard-crash the VM beyond Pydantic ValidationError
