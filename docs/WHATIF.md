# What-If Simulator

The DiaTwin What-If Simulator enables interactive, personalized scenario testing for a patient based on their digital twin state.

## Architecture

1. **State Estimation**: Reconstructs the unobserved physiological state (gut compartments, physiological noise, exercise effect) using a Luenberger-type observer on the patient's recent history.
2. **Personalization**: Estimates 5 patient-specific physiological parameters via Maximum A Posteriori (MAP) estimation:
   - `fasting_glucose_baseline`
   - `dawn_amplitude`
   - `carb_sensitivity`
   - `glucose_decay_rate`
   - `exercise_sensitivity`
3. **Prior**: Uses an empirical population prior derived from EHR features to regularize parameter estimates, especially for patients with sparse data.
4. **Scenario Engine**: Deterministically simulates branching futures (Baseline vs. Scenario) and compares key metrics (Peak, Time Above 180).

## Safety & Constraints

- **No Medical Scenarios**: The simulator is explicitly programmed to reject any scenarios involving insulin dosing, medication changes, or any clinical interventions.
- **Identifiability Checks**: If a patient lacks sufficient meal or exercise history, the simulator flags the relevant sensitivity parameter as unidentifiable, defaults heavily to the population prior, and downgrades the confidence score of the simulation.

## Evaluation (In-Silico Oracle)

We evaluate the simulator's accuracy using an Oracle: since we know the true hidden generating parameters of the synthetic patients, we can directly reconstruct the exact ground-truth effect of a scenario. 

**Metrics on TEST:**
- `peak_err`: The mean absolute error between the simulator's median estimated peak glucose and the Oracle's true peak.
- `peak_covered`: The percentage of time the Oracle's true peak change falls within the simulator's [p10, p90] uncertainty interval.

For the What-if Simulator test evaluation (6 test patients), the peak error is 1.0, 10.2 and 11.5 mg/dL for the three tested scenarios (reports/WHATIF_TEST_DONE.json). The 80% interval coverage is 0%, 17% and 0%. The uncertainty bands significantly under-cover. Integrity note: for the what-if module, the manifest and the test marker were committed together so freeze-before-test cannot be shown from git.

## Usage

```python
from src.simulator.scenarios import WhatIfRequest, PlannedMeal
from src.twin.loader import TwinRegistry

registry = TwinRegistry(config)
twin = registry.get("P007")

request = WhatIfRequest(
    planned_meals=[PlannedMeal(time_offset_min=15, carbs_g=50)],
    scenario_names=["walk_30min_moderate"]
)

report = twin.run_whatif(request)
print(report.scenarios[0].summary_sentence)
```
