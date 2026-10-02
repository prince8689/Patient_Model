import json

with open('docs/data_quality.json') as f:
    r = json.load(f)

card = f'''# Data Card: DiaTwin Synthetic Dataset

## Dataset overview
Synthetic timeseries dataset of continuous glucose monitoring, heart rate, and behavior data for Type 2 Diabetes patients.
- Patients: {r['patients']}
- Total Rows: {r['rows']}
- Date Range: {r['date_range'][0]} to {r['date_range'][1]}
- Class Balance Overall: {r['class_balance_overall_pct']:.2f}% positive

## Provenance
Fully synthetic. Generated via `generate_patients.py` and `generate_wearable.py` using NumPy seeded rng (seed 42).

## Files and schemas
- `data/raw/patients.csv`: EHR features (age, sex, bmi, hba1c, meds, diabetes_duration).
- `data/raw/wearable.csv`: Timeseries (glucose, HR, steps, sleep, meals, activity).
- `data/processed/labels.csv`: Ground truth for predicting glucose spikes.
- `data/processed/splits.csv`: Patient to split assignment.

## Label definition and exclusions
`spike_next_2h`: 1 if maximum observed glucose in the next 120 minutes >= current glucose + 50 mg/dL, else 0.
Rows are excluded (valid=0, label=NaN) if current glucose is missing, or if >20% of the future window is missing.

## Split strategy
Patient-wise splitting (no patient overlaps between splits) to prevent data leakage and ensure generalization.
- Train (70%): {r['class_balance_splits_pct']['train']:.2f}% positive
- Validation (15%): {r['class_balance_splits_pct']['val']:.2f}% positive
- Test (15%): {r['class_balance_splits_pct']['test']:.2f}% positive

## Known limitations and biases
- Synthetic data: physiology is simplified (e.g., discrete carb compartments, fixed linear combinations).
- Fixed 5-minute sampling interval.
- Represents only Type 2 Diabetes.

## Intended use
Prototyping prediction pipelines, algorithm evaluation, and dashboard building for the Digital Twin Challenge.

## Not intended for
Clinical use or real-world physiological diagnosis.
'''

with open('docs/DATA_CARD.md', 'w') as f:
    f.write(card)

with open('docs/SPEC.md', 'a', encoding='utf-8') as f:
    f.write('\n## 15. Label and Split Definition\n')
    f.write('- **Label**: `spike_next_2h` = 1 if max future 2h observed glucose >= current + 50mg/dL.\n')
    f.write('- **Split Strategy**: Patient-wise to ensure 0 data leakage. 70/15/15 ratio stratified by HbA1c.\n')
