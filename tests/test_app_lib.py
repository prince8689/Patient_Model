import pytest
from src.app_lib.data_access import get_demo_patients, get_patient_timeline
from src.app_lib.viewmodels import patient_overview, twin_view
from src.app_lib.moments import available_moments, step_time, next_alert
import pandas as pd
from unittest.mock import patch

def test_data_access():
    pids = get_demo_patients()
    assert isinstance(pids, list)
    if pids:
        tl = get_patient_timeline(pids[0])
        assert not tl.empty
        assert "data_status" in tl.columns

def test_patient_overview():
    pids = get_demo_patients()
    if not pids:
        pytest.skip("No demo patients")
    df = patient_overview()
    assert not df.empty
    assert "patient_id" in df.columns
    assert "data_status" in df.columns
    
    # Static scan check
    forbidden = ["archetype", "baseline_insulin_sensitivity"]
    for c in forbidden:
        assert c not in df.columns
        
def test_twin_view_and_moments():
    pids = get_demo_patients()
    if not pids:
        pytest.skip("No demo patients")
        
    pid = pids[0]
    moms = available_moments(pid)
    assert moms
    
    # Test step
    m0 = moms[0]
    next_m = step_time(pid, m0, 5)
    assert next_m >= m0
    
    # Test view
    view = twin_view(pid, m0)
    assert "profile" in view
    assert "kpis" in view
    assert "forecast" in view
    
    # Static scan
    forbidden = ["spike_next_2h", "future_max_glucose", "sim_params"]
    assert "archetype" not in str(view)
