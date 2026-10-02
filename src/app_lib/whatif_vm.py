import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from src.app_lib.data_access import get_config, get_registry
from src.simulator.scenarios import PlannedActivity, PlannedMeal, WhatIfRequest


def available_scenarios() -> list[dict[str, Any]]:
    config = get_config()
    scenarios = config.get("whatif", {}).get("scenarios", {})
    
    res = []
    for name, spec in scenarios.items():
        needs_meal = name in ["meal_earlier_30min", "meal_later_30min", "reduce_carbs_30pct", "split_meal_60min", "walk_10min_after_meal", "walk_30min_moderate"]
        if "walk" in name and "after_meal" not in name:
            needs_meal = False
            
        label = name.replace("_", " ").capitalize()
        desc = f"Simulates {label}"
        
        res.append({
            "name": name,
            "label": label,
            "description": desc,
            "needs_meal": needs_meal,
            "parameters": spec
        })
    return res

def build_request(plan_meals: list[dict], selected_scenarios: list[str], custom_params: dict) -> tuple[WhatIfRequest | None, list[str]]:
    errors = []
    
    # Check for forbidden keywords
    forbidden = ["insulin", "medication", "dose", "drug", "metformin"]
    for k in custom_params:
        if any(f in k.lower() for f in forbidden):
            errors.append(f"Invalid parameter '{k}': Insulin and medication dosing scenarios are strictly prohibited.")
            
    for m in plan_meals:
        for k, v in m.items():
            if isinstance(k, str) and any(f in k.lower() for f in forbidden):
                errors.append(f"Invalid parameter in meal '{k}': Medical dosing is strictly prohibited.")
            if isinstance(v, str) and any(f in str(v).lower() for f in forbidden):
                errors.append(f"Invalid parameter value '{v}': Medical dosing is strictly prohibited.")
                
    if errors:
        return None, errors
        
    req = WhatIfRequest(scenario_names=selected_scenarios)
    for m in plan_meals:
        carbs = m.get("carbs_g", 0)
        offset = m.get("offset_min", 0)
        if carbs < 0 or carbs > 200:
            errors.append(f"Meal carbs must be 0-200g, got {carbs}")
        if offset < 0 or offset > 180:
            errors.append(f"Meal offset must be 0-180 min, got {offset}")
        req.planned_meals.append(PlannedMeal(time_offset_min=int(offset), carbs_g=float(carbs)))
        
    if "custom_activity" in custom_params:
        a = custom_params["custom_activity"]
        dur = a.get("duration", 0)
        intensity = a.get("intensity", 1)
        offset = a.get("offset_min", 0)
        if dur > 0:
            if dur < 5 or dur > 120:
                errors.append(f"Activity duration must be 5-120 min, got {dur}")
            if intensity < 0 or intensity > 5:
                errors.append(f"Activity intensity must be 0-5, got {intensity}")
            req.baseline_activities.append(PlannedActivity(start_offset_min=int(offset), duration_min=int(dur), intensity=int(intensity)))

    if errors:
        return None, errors
        
    return req, []

@st.cache_data(ttl=3600, show_spinner=False)
def run_whatif_view(patient_id: str, as_of: datetime, req_dict: dict) -> dict[str, Any]:
    import time
    t0 = time.time()
    
    registry = get_registry()
    if registry.whatif_artifacts is None:
        raise RuntimeError("What-if simulator unavailable: frozen artifacts missing.")
        
    twin = registry.get(patient_id)
    
    # Reconstruct request from dict (for cacheability)
    req = WhatIfRequest(scenario_names=req_dict.get("scenario_names", []))
    for m in req_dict.get("planned_meals", []):
        req.planned_meals.append(PlannedMeal(m["time_offset_min"], m["carbs_g"]))
    for a in req_dict.get("baseline_activities", []):
        req.baseline_activities.append(PlannedActivity(a["start_offset_min"], a["duration_min"], a["intensity"]))
        
    # We must ingest data exactly up to as_of (NO FUTURE PEEKING)
    from src.app_lib.data_access import get_patient_wearable
    wearable = get_patient_wearable(patient_id)
    wearable = wearable[wearable["timestamp"] <= as_of]
    
    # Ingest the last 500 samples (sufficient for warmup and history buffer)
    samples = wearable.to_dict(orient="records")
    cutoff_samples = samples[-500:] if len(samples) > 500 else samples
    
    for s in cutoff_samples[:-1]:
        twin.ingest(s)
    state = twin.ingest(cutoff_samples[-1])
    
    # Run what_if
    report = twin.what_if(req)
    
    compute_time = time.time() - t0
    
    # Convert to pure dict
    res = {
        "metadata": {
            "patient_id": patient_id,
            "as_of": as_of.isoformat(),
            "compute_time_sec": compute_time,
            "confidence_level": report.confidence_level,
            "confidence_reasons": report.confidence_reasons,
            "forecast_agreement": report.forecast_agreement_note
        },
        "ranking": report.ranking,
        "baseline": report.baseline.__dict__,
        "scenarios": [s.__dict__ for s in report.scenarios],
        "history_window": {
            "glucose": twin.buffer[-48:] if len(twin.buffer) >= 48 else twin.buffer
        }
    }
    
    # Filter ranking based on confidence
    config = get_config()
    min_conf = config["app"].get("ranking_min_confidence", "medium")
    if min_conf == "high" and report.confidence_level != "High" or min_conf == "medium" and report.confidence_level not in ["High", "Medium"]:
        res["ranking"] = []
        
    return res

def validation_summary() -> dict[str, Any] | None:
    
    val_path = Path("reports/metrics_whatif_val.json")
    test_path = Path("reports/metrics_whatif_test_day10.json")
    
    metrics = {}
    
    if val_path.exists():
        with open(val_path, "r") as f:
            metrics["validation"] = json.load(f)
            
    if test_path.exists():
        with open(test_path, "r") as f:
            metrics["test"] = json.load(f)
            
    if not metrics:
        return None
        
    return metrics

def export_whatif_json(report_dict: dict) -> str:
    return json.dumps(report_dict, indent=2)
