# Realism Comparison

This document compares the synthetic cohort against the real data (Shanghai T2DM dataset).

## Metrics Table
| Metric | Real | Synthetic |
|---|---|---|
| Patients | 100 | 40 |
| Recordings | 109 | 40 |
| Observed Samples | 112103 | 78592 |
| Total Slots | 112448 | 80639 |
| Mean Glucose (mg/dL) | 141.10 | 219.30 |
| Std Glucose (mg/dL) | 40.67 | 43.64 |
| CV Glucose | 0.2867 | 0.2028 |
| Time Below 70 (%) | 0.0231 | 0.0089 |
| Time 70-180 (%) | 0.7808 | 0.3050 |
| Time Above 180 (%) | 0.1962 | 0.6861 |
| Label Prevalence | 0.1386 | 0.1401 |
| Age | 60.2 | 54.6 |
| BMI | 24.1 | 29.7 |
| HbA1c | 9.10 | 8.76 |
| Insulin Use | 0.3200 | 0.2250 |
| Gap Count (15m grid) | 76 | 1361 |
| Gap Median (min) | 30.0 | 15.0 |
| Gap Mean (min) | 68.1 | 22.6 |
| Gaps per 1000 slots | 0.68 | 16.88 |
| Gaps per patient-day | 0.06 | 1.62 |
| Share Missing Slots | 0.0031 | 0.0254 |
| Meal Rise (mg/dL) | not computable on real data: no exact meal timestamp exists. Raw meal fields: ['patient_id', 'recording_id', 'timestamp', 'dietary_intake_text', 'carbs_g'] | 60.77 |

## Metric-by-metric reading

### HbA1c Regression
For both cohorts:
- **Real Data**: patients used: 92, handling of missing HbA1c: dropped. Regression slope: 5.86, intercept: 88.11, R-squared: 0.2574. The glucose mean predicted by 28.7 x HbA1c - 46.7 is 214.33 mg/dL, while the observed mean is 141.40 mg/dL.
- **Synthetic Data**: patients used: 40, handling of missing HbA1c: dropped. Regression slope: 42.94, intercept: -156.98, R-squared: 0.7182. The glucose mean predicted by 28.7 x HbA1c - 46.7 is 204.81 mg/dL, while the observed mean is 219.30 mg/dL.

![HbA1c Regression](hba1c_scatter.png)

### Hour-of-Day Glucose Profile
![Hour of day mean glucose comparison](hour_profile_comparison.png)

## Changes a new synthetic cohort needs
1. Mean Glucose and Time Above 180: The synthetic mean glucose (219.30) is 78.20 mg/dL higher than real (141.10). Time above 180 must drop from 0.6861 to 0.1962.
2. Gap Statistics: Synthetic gaps per 1000 slots (16.88) are significantly higher than real (0.68). The generation should produce fewer gaps, but with a longer median length (currently 15.0 vs 30.0 mins).
3. HbA1c to Mean Glucose Regression: The synthetic slope (42.94) is much steeper than the real cohort (5.86). The generator should flatten this relationship.
4. Demographics: BMI should be shifted closer to 24.1 (currently 29.7). Age should increase slightly to 60.2 (currently 54.6). Insulin usage should increase from 0.2250 to 0.3200.
5. Missing Meal Markers: The synthetic data generates precise meal rises, whereas real data lacks exact meal timestamps.