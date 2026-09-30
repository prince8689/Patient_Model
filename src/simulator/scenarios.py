from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PlannedMeal:
    time_offset_min: int
    carbs_g: float

@dataclass
class PlannedActivity:
    start_offset_min: int
    duration_min: int
    intensity: float

@dataclass
class ScenarioSpec:
    name: str
    label: str
    description: str
    transformations: dict

@dataclass
class WhatIfRequest:
    planned_meals: List[PlannedMeal] = field(default_factory=list)
    baseline_activities: List[PlannedActivity] = field(default_factory=list)
    scenario_names: List[str] = field(default_factory=list)
    horizon: int = 180

def validate_request(request: WhatIfRequest, config: dict):
    for m in request.planned_meals:
        if m.carbs_g < 0 or m.carbs_g > 200:
            raise ValueError(f"Meal carbs must be 0-200g, got {m.carbs_g}")
        if m.time_offset_min < 0 or m.time_offset_min > request.horizon:
            raise ValueError("Meal must be within horizon")
            
    for a in request.baseline_activities:
        if a.duration_min < 5 or a.duration_min > 120:
            raise ValueError("Activity duration must be 5-120 min")
        if a.intensity < 0 or a.intensity > 5:
            raise ValueError("Activity intensity must be 0-5")
            
    valid_scenarios = config["whatif"]["scenarios"].keys()
    for s in request.scenario_names:
        if s not in valid_scenarios:
            raise ValueError(f"Scenario {s} not permitted. Allowed: {list(valid_scenarios)}. Insulin and medication dosing scenarios are STRICTLY PROHIBITED.")

def apply_scenario(request: WhatIfRequest, scenario_name: str, config: dict) -> tuple[List[PlannedMeal], List[PlannedActivity]]:
    spec = config["whatif"]["scenarios"][scenario_name]
    
    meals = [PlannedMeal(m.time_offset_min, m.carbs_g) for m in request.planned_meals]
    activities = [PlannedActivity(a.start_offset_min, a.duration_min, a.intensity) for a in request.baseline_activities]
    
    if not meals and scenario_name in ["meal_earlier_30min", "meal_later_30min", "reduce_carbs_30pct", "split_meal_60min"]:
        # Not applicable if no meals
        return meals, activities
        
    if "shift" in spec:
        for m in meals:
            m.time_offset_min += spec["shift"]
            m.time_offset_min = max(0, min(m.time_offset_min, request.horizon))
            
    if "factor" in spec:
        for m in meals:
            m.carbs_g *= spec["factor"]
            
    if "first_fraction" in spec and "gap" in spec:
        if meals:
            m = meals[0]
            fraction = spec["first_fraction"]
            gap = spec["gap"]
            m2 = PlannedMeal(m.time_offset_min + gap, m.carbs_g * (1 - fraction))
            m.carbs_g *= fraction
            meals.append(m2)
            
    if "duration" in spec:
        if "start_after_meal_min" in spec and meals:
            start = meals[0].time_offset_min + spec["start_after_meal_min"]
        else:
            start = 0 
        activities.append(PlannedActivity(start, spec["duration"], spec["intensity"]))
        
    return meals, activities
