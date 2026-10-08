# Realism Comparison

This document compares the synthetic cohort against the real data (Shanghai T2DM dataset).

## Metrics Table
| Metric | Real | Synthetic |
|---|---|---|
| Patients | 100 | 40 |
| Recordings | 109 | 40 |
| Observed Samples | 112133 | 78592 |
| Total Slots | 112448 | 80639 |
| Mean Glucose (mg/dL) | 141.18 | 219.30 |
| Std Glucose (mg/dL) | 40.81 | 43.64 |
| CV Glucose | 0.2873 | 0.2028 |
| Time Below 70 (%) | 0.0231 | 0.0089 |
| Time 70-180 (%) | 0.7806 | 0.3050 |
| Time Above 180 (%) | 0.1964 | 0.6861 |
| Label Prevalence | 0.1194 | 0.1401 |
| Age | 60.2 | 54.6 |
| BMI | 24.1 | 29.7 |
| HbA1c | 9.10 | 8.76 |
| Insulin Use | 0.3200 | 0.2250 |
| Gap Count (15m grid) | 68 | 1361 |
| Gap Median (min) | 30.0 | 15.0 |
| Gap Mean (min) | 69.5 | 22.6 |
| Gaps per 1000 slots | 0.60 | 16.88 |
| Gaps per patient-day | 0.06 | 1.62 |
| Share Missing Slots | 0.0028 | 0.0254 |

## Metric-by-metric reading

### HbA1c Regression
For both cohorts:
- **Real Data**: patients used: 92, handling of missing HbA1c: dropped. Regression slope: 5.88, intercept: 88.00, R-squared: 0.2576. The glucose mean predicted by 28.7 x HbA1c - 46.7 is 214.33 mg/dL, while the observed mean is 141.49 mg/dL.
- **Synthetic Data**: patients used: 40, handling of missing HbA1c: dropped. Regression slope: 42.94, intercept: -156.98, R-squared: 0.7182. The glucose mean predicted by 28.7 x HbA1c - 46.7 is 204.81 mg/dL, while the observed mean is 219.30 mg/dL.

**Observation**: At the real cohort's mean HbA1c, the formula 28.7 x HbA1c - 46.7 gives about 214 mg/dL, while the observed mean glucose is about 141 mg/dL. Possible hypotheses for this discrepancy (which need checking against the dataset paper) could include:
- The CGM device calibration or interstitial delay may systematically underreport true blood glucose.
- The sampled days may not be representative of the previous 3 months (e.g. patients improved diet when put on monitors).
- Severe missingness during high-glucose periods.

![HbA1c Regression](hba1c_scatter.png)

### Hour-of-Day Glucose Profile
![Hour of day mean glucose comparison](hour_profile_comparison.png)

## Changes a new synthetic cohort needs
1. **Gap Statistics (15m grid)**: Synthetic gaps per 1000 slots (16.88) are much higher than real (0.60). The generator should produce fewer gaps, but with longer median length (15.0 vs 30.0 mins).
2. **HbA1c to Mean Glucose Slope**: The synthetic slope (42.94) is much steeper than the real cohort (5.88). The generator should flatten this relationship.
3. **Hour-of-Day Profile**: The synthetic profile peaks at 23:00 (246.89) and is lowest at 19:00 (199.10). The real profile peaks at 8:00 (169.59) and is lowest at 3:00 (114.50).
4. **Time Below 70**: The synthetic time below 70 (0.0089) is lower than the real cohort (0.0231).
5. **Mean Glucose (mg/dL) and Time Above 180**: The synthetic mean glucose (219.30) is significantly higher than real (141.18). Time above 180 must drop from 0.6861 to 0.1964.
6. **Insulin Use**: Synthetic insulin use (0.2250) is lower than real (0.3200).
7. **Coefficient of Variation (CV)**: The synthetic CV (0.2028) is lower than the real CV (0.2873), meaning the synthetic glucose is less variable relative to its mean.
8. **BMI**: Synthetic BMI (29.7) is higher than real (24.1).
9. **Age**: Synthetic Age (54.6) is lower than real (60.2).
