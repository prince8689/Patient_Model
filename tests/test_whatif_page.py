import pytest
from src.app_lib.whatif_vm import build_request, run_whatif_view, available_scenarios
from datetime import datetime
import pandas as pd
from pathlib import Path
import json

def test_build_request_rejects_forbidden():
    meals = [{"offset_min": 0, "carbs_g": 50}]
    scenarios = ["baseline"]
    
    # Insulin in key
    custom = {"insulin_dose": 10}
    req, errs = build_request(meals, scenarios, custom)
    assert req is None
    assert any("insulin" in e.lower() for e in errs)
    
    # Medication in meal
    meals_bad = [{"offset_min": 0, "carbs_g": 50, "note": "take medication"}]
    req, errs = build_request(meals_bad, scenarios, {})
    assert req is None
    assert any("medical dosing" in e.lower() for e in errs)
    
def test_build_request_rejects_out_of_range():
    meals = [{"offset_min": -10, "carbs_g": 300}]
    req, errs = build_request(meals, ["baseline"], {})
    assert req is None
    assert any("0-200g" in e for e in errs)
    assert any("0-180" in e for e in errs)

def test_static_scan_no_oracle_leakage():
    # SCAN all files in app/ and src/app_lib/
    app_files = list(Path("app").rglob("*.py")) + list(Path("src/app_lib").rglob("*.py"))
    
    forbidden_terms = [
        "patient_sim_params", 
        "archetype", 
        "baseline_insulin_sensitivity", 
        "spike_next_2h", 
        "future_max_glucose",
        "src.evaluation.oracle"
    ]
    
    for fp in app_files:
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
            for term in forbidden_terms:
                assert term not in content, f"Forbidden term '{term}' found in {fp}"

def test_safety_wording_scan():
    app_files = list(Path("app").rglob("*.py")) + list(Path("src/app_lib").rglob("*.py"))
    
    forbidden_phrases = [
        "you should", 
        "take insulin", 
        "increase your dose", 
        "recommend that you", 
        "we recommend"
    ]
    
    for fp in app_files:
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read().lower()
            for phrase in forbidden_phrases:
                assert phrase not in content, f"Forbidden phrase '{phrase}' found in {fp}"

@pytest.mark.filterwarnings("ignore")
def test_run_whatif_view_no_future_peeking(monkeypatch):
    # Ensure that run_whatif_view only sees data up to as_of
    # We mock twin_registry and check get_patient_wearable call
    
    mock_wearable = pd.DataFrame({
        "patient_id": ["P007"] * 100,
        "timestamp": pd.date_range("2026-01-01 00:00", periods=100, freq="5min"),
        "glucose_mgdl": [100] * 100
    })
    
    as_of = pd.to_datetime("2026-01-01 04:00") # step 48
    
    monkeypatch.setattr("src.app_lib.data_access.get_patient_wearable", lambda pid: mock_wearable)
    
    class DummyTwin:
        def __init__(self):
            self.buffer = []
            self.last_ts = None
        def ingest(self, s):
            self.buffer.append(s)
            self.last_ts = s["timestamp"]
            return {}
        def what_if(self, req):
            from src.simulator.whatif import WhatIfReport, ScenarioResult
            return WhatIfReport(
                timestamp=str(self.last_ts),
                confidence_level="High",
                confidence_reasons=[],
                baseline=ScenarioResult(
                    name="baseline",
                    median_trajectory=[100]*36,
                    p10_trajectory=[90]*36,
                    p90_trajectory=[110]*36,
                    peak_median=100, peak_p10=90, peak_p90=110,
                    mean_median=100, mean_p10=90, mean_p90=110,
                    time_above_180_median=0, time_above_180_p10=0, time_above_180_p90=0,
                    time_below_70_median=0, time_below_70_p10=0, time_below_70_p90=0,
                    spike_prob=0.0, hypo_risk=False
                ),
                scenarios=[],
                ranking=["baseline"]
            )
            
    dummy = DummyTwin()
    
    class DummyRegistry:
        whatif_artifacts = True
        def get(self, pid): return dummy
        
    monkeypatch.setattr("src.app_lib.whatif_vm.get_registry", lambda: DummyRegistry())
    
    res = run_whatif_view("P007", as_of, {"scenario_names": ["baseline"]})
    
    # Check that twin only ingested data up to as_of
    assert pd.to_datetime(dummy.last_ts) <= as_of
    assert len(dummy.buffer) == min(49, 500)
    
    # Check bands ordering
    b = res["baseline"]
    assert b["p10_trajectory"][0] <= b["median_trajectory"][0] <= b["p90_trajectory"][0]

def test_app_smoke():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("../app/pages/3_What_If_Simulator.py")
    # Setting session state to avoid early stop
    at.session_state["patient_id"] = "P007"
    at.session_state["as_of"] = pd.to_datetime("2026-01-03 21:50")
    
    at.run()
    assert not at.exception
