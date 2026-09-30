import pytest
import pandas as pd
import numpy as np
from src.utils.config import load_config
from src.simulator.scenarios import WhatIfRequest, PlannedMeal, PlannedActivity, validate_request, apply_scenario
from src.simulator.whatif import run_whatif

def test_whatif_validation():
    config = load_config()
    
    # Valid
    req = WhatIfRequest(
        planned_meals=[PlannedMeal(15, 50)],
        scenario_names=["walk_30min_moderate"]
    )
    validate_request(req, config)
    
    # Invalid meal (carbs > 200)
    req2 = WhatIfRequest(planned_meals=[PlannedMeal(15, 250)])
    with pytest.raises(ValueError, match="0-200g"):
        validate_request(req2, config)
        
    # Insulin scenario should throw error
    req3 = WhatIfRequest(scenario_names=["take_insulin"])
    with pytest.raises(ValueError, match="PROHIBITED"):
        validate_request(req3, config)

def test_apply_scenario():
    config = load_config()
    req = WhatIfRequest(
        planned_meals=[PlannedMeal(15, 50)],
        scenario_names=["split_meal_60min"]
    )
    meals, _ = apply_scenario(req, "split_meal_60min", config)
    assert len(meals) == 2
    assert meals[0].time_offset_min == 15
    assert meals[0].carbs_g == 25
    assert meals[1].time_offset_min == 75
    assert meals[1].carbs_g == 25
    
    req2 = WhatIfRequest(
        planned_meals=[PlannedMeal(15, 50)],
        scenario_names=["walk_30min_moderate"]
    )
    meals, acts = apply_scenario(req2, "walk_30min_moderate", config)
    assert len(meals) == 1
    assert len(acts) == 1
    assert acts[0].start_offset_min == 30 # 15 + 15
    assert acts[0].duration_min == 30

def test_run_whatif_mock():
    config = load_config()
    req = WhatIfRequest(
        planned_meals=[PlannedMeal(15, 50)],
        scenario_names=["walk_30min_moderate"]
    )
    
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01 08:00", periods=24*12, freq="5min"),
        "glucose_mgdl": np.random.uniform(90, 110, size=24*12)
    })
    
    prof = {"age": 50, "bmi": 25, "hba1c": 6.5, "diabetes_duration_years": 5, "on_insulin": 0, "on_metformin": 1, "hypertension": 0}
    prior = {
        "mean": {"baseline": 100.0, "dawn_amp": 0.0, "carb_sens": 1.0, "decay": 0.05, "ex_sens": 1.0},
        "cov": np.eye(5) * 0.1
    }
    
    report = run_whatif(df, prof, req, prior, config)
    assert report.baseline.name == "baseline"
    assert len(report.scenarios) == 1
    assert report.scenarios[0].name == "walk_30min_moderate"
    assert "walk_30min_moderate" in report.ranking
