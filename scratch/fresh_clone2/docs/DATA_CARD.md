# Data Card: DiaTwin Synthetic Dataset

## Dataset overview
Synthetic timeseries dataset of continuous glucose monitoring, heart rate, and behavior data for Type 2 Diabetes patients.
- Patients: 40
- Total Rows: 241920
- Date Range: 2026-01-01 00:00:00 to 2026-01-21 23:55:00
- Class Balance Overall: 14.01% positive

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
- Train (70%): 13.80% positive
- Validation (15%): 14.24% positive
- Test (15%): 14.76% positive

## Known limitations and biases
- Synthetic data: physiology is simplified (e.g., discrete carb compartments, fixed linear combinations).
- Fixed 5-minute sampling interval.
- Represents only Type 2 Diabetes.

## Intended use
Prototyping prediction pipelines, algorithm evaluation, and dashboard building for the Digital Twin Challenge.

## Not intended for
Clinical use or real-world physiological diagnosis.

## Real Data Comparison
See [REAL_DATA.md](REAL_DATA.md) for information on the real dataset used for comparison.
