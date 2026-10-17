# Realism Comparison

This document compares the synthetic cohort against the real data (Shanghai T2DM dataset).

## Metrics Table
| Metric | Real | Synthetic |
|---|---|---|
| Patients | 100 | 40 |
| Recordings | 109 | 40 |
| Observed Samples | 112462 | 78592 |
| Total Slots | 112489 | 80639 |
| Mean Glucose (mg/dL) | 141.01 | 219.30 |
| Std Glucose (mg/dL) | 40.91 | 43.64 |
| CV Glucose | 0.2889 | 0.2028 |
| Time Below 70 (%) | 0.0253 | 0.0089 |
| Time 70-180 (%) | 0.7784 | 0.3050 |
| Time Above 180 (% patient-level average) | 0.1963 | 0.6861 |
| Label Prevalence | 0.1386 | 0.1401 |
| Age | 60.2 | 54.6 |
| BMI | 24.1 | 29.7 |
| HbA1c | 9.10 | 8.76 |
| Insulin Use | 0.3200 | 0.2250 |
| Gap Count (15m grid) | 11 | 1361 |
| Gap Median (min) | 15.0 | 15.0 |
| Gap Mean (min) | 36.8 | 22.6 |
| Gaps per 1000 slots | 0.10 | 16.88 |
| Gaps per patient-day | 0.01 | 1.62 |
| Share Missing Slots | 0.0002 | 0.0254 |

## Metric-by-metric reading

### HbA1c Regression
For both cohorts:
- **Real Data**: patients used: 92, handling of missing HbA1c: dropped. Regression slope: 5.96, intercept: 87.11, R-squared: 0.2590. The glucose mean predicted by 28.7 x HbA1c - 46.7 is 214.33 mg/dL, while the observed mean is 141.31 mg/dL.
- **Synthetic Data**: patients used: 40, handling of missing HbA1c: dropped. Regression slope: 42.94, intercept: -156.98, R-squared: 0.7182. The glucose mean predicted by 28.7 x HbA1c - 46.7 is 204.81 mg/dL, while the observed mean is 219.30 mg/dL.

**Observation**: At the real cohort's mean HbA1c, the formula 28.7 x HbA1c - 46.7 gives about 214 mg/dL, while the observed mean glucose is about 141 mg/dL. Possible hypotheses for this discrepancy (which need checking against the dataset paper) could include:
- The CGM device calibration or interstitial delay may systematically underreport true blood glucose.
- The sampled days may not be representative of the previous 3 months (e.g. patients improved diet when put on monitors).
- Severe missingness during high-glucose periods.

![HbA1c Regression](hba1c_scatter.png)

### Hour-of-Day Glucose Profile
![Hour of day mean glucose comparison](hour_profile_comparison.png)

### Sensor Limits and Valid Range
Under the valid range of 39.5 to 500.5 mg/dL in configs/real_data.yaml, 329 readings at the sensor lower limit (39.6 mg/dL, 2.2 mmol/L) are kept with a censored flag; 30 readings above 400 mg/dL (maximum 468) were kept. The loader code keeps all 112462 readings (reports/real_data_quality.json, key total_glucose_samples_final: 112462). This matches the kept floor variant in reports/real_range_check.json: patient-level mean glucose is 141.01 mg/dL (key patient_level_mean_glucose.with_floor; 141.18 mg/dL if excluded), patient-level time below 70 is 0.0253 (key time_below_70_with_floor.per_patient; 0.0231 if excluded), and patient-level time above 180 is 0.1963 (19.63%), defined as the patient-level average of the fraction of readings exceeding 180 mg/dL across all 100 patients (pooled share is 0.1890 / 18.90%; candidate_range_details key 39 to 501, time_above_180_per_patient). While reports/realism_comparison.json records real_counts.samples as 112462 (matching the kept floor variant), it does not store mean glucose or time below 70 keys directly; the values cited here come from the matching variant in reports/real_range_check.json.

## Changes a new synthetic cohort needs
1. **Gap Statistics (15m grid)**: Synthetic gaps per 1000 slots (16.88) are much higher than real (0.10). The generator should produce fewer gaps, but with longer median length (15.0 vs 15.0 mins).
2. **HbA1c to Mean Glucose Slope**: The synthetic slope (42.94) is much steeper than the real cohort (5.96). The generator should flatten this relationship.
3. **Hour-of-Day Profile**: The synthetic profile peaks at 23:00 (246.89) and is lowest at 19:00 (199.10). The real profile peaks at 8:00 (169.36) and is lowest at 3:00 (113.90).
4. **Time Below 70**: The synthetic time below 70 (0.0089) is lower than the real cohort (0.0253).
5. **Mean Glucose (mg/dL) and Time Above 180**: The synthetic mean glucose (219.30) is significantly higher than real (141.01). Time above 180 must drop from 0.6861 to 0.1963.
6. **Coefficient of Variation (CV)**: The synthetic CV (0.2028) is lower than the real CV (0.2889), meaning the synthetic glucose is less variable relative to its mean.
7. **Insulin Use**: Synthetic insulin use (0.2250) is lower than real (0.3200).
8. **BMI**: Synthetic BMI (29.7) is higher than real (24.1).
9. **Age**: Synthetic Age (54.6) is lower than real (60.2).
