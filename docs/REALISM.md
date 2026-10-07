# Realism Comparison

This document compares the synthetic cohort against the real data (Shanghai T2DM dataset).

## Counts
| Metric | Real | Synthetic |
|---|---|---|
| Patients | 100 | 40 |
| Recordings | 109 | 40 |
| Observed Samples | 112103 | 78592 |
| Total Slots | 112448 | 80639 |

## Metrics Table

| Metric | Real | Synthetic | Distance |
|---|---|---|---|
| Mean Glucose (mg/dL) | 141.10 | 219.30 | 78.20 |
| Std Glucose (mg/dL) | 40.67 | 43.64 | 2.97 |
| CV Glucose | 0.2867 | 0.2028 | 0.0838 |
| Time Below 70 (%) | 0.0231 | 0.0089 | 0.0142 |
| Time 70-180 (%) | 0.7808 | 0.3050 | 0.4758 |
| Time Above 180 (%) | 0.1962 | 0.6861 | 0.4900 |
| Label Prevalence | 0.1386 | 0.1401 | 0.0015 |
| Age | 60.2 | 54.6 | 5.6 |
| BMI | 24.1 | 29.7 | 5.6 |
| HbA1c | 9.10 | 8.76 | 0.33 |
| Insulin Use | 0.3200 | 0.2250 | 0.0950 |
| Meal Rise (mg/dL) | not computable on real data: no exact meal timestamp exists. Raw meal fields: ['patient_id', 'recording_id', 'timestamp', 'dietary_intake_text', 'carbs_g'] | 60.77 | N/A |
| Gap Count (15m grid) | 76 | 1361 | 1285 |
| Gap Median (15m grid, min) | 30.0 | 15.0 | 15.0 |
| Gap Mean (15m grid, min) | 68.1 | 22.6 | 45.5 |
| Gaps per 1000 slots | 0.68 | 16.88 | 16.20 |
| Gaps per patient-day | 0.06 | 1.62 | 1.56 |
| Share Missing Slots | 0.0031 | 0.0254 | 0.0223 |
| Regression Slope (HbA1c to mean glucose) | 5.86 | 42.94 | 37.08 |
| Regression Intercept | 88.11 | -156.98 | 245.09 |
| Regression R-squared | 0.2574 | 0.7182 | 0.4608 |

## Hour of Day Profile

![Hour of day mean glucose comparison](hour_profile_comparison.png)

## Required Changes for a New Synthetic Cohort

To improve realism, a new synthetic cohort needs:
1. Target mean glucose must be closer to 141.1 mg/dL, and time above 180 should be reduced from 68.6% to match the observed 19.6%.
2. The HbA1c to mean glucose relationship needs flattening. The real slope is 5.86 compared to synthetic 42.94.
3. The average BMI in the real cohort is 24.1, which is 5.6 different from synthetic.
4. The average age is 60.2 years.
5. The insulin usage should be closer to 32.0%.
6. The gap generation needs fewer but longer sensor outages (real gaps per 1000 slots: 0.68, synthetic: 16.88).
