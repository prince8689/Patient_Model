# Realism Comparison

This document details the realism of the DiaTwin synthetic dataset compared to a real Type 2 Diabetes dataset (ShanghaiT2DM). The comparison uses matching subsets consisting only of TRAIN and VALIDATION patients, ensuring real test rows are never accessed.

The previous comparison used 100 real patients (including test rows implicitly) and the full synthetic dataset. This rerun uses exactly 87 real patients (14285 samples) and 28 synthetic patients (56448 samples, resampled to 15-minute grid).

## Profile Attributes
| Metric | Real (ShanghaiT2DM) | Synthetic (DiaTwin) | Wasserstein Distance |
| :--- | :--- | :--- | :--- |
| Age | 59.97 | 54.25 | 8.00 |
| BMI | 24.27 | 29.76 | 5.49 |
| HbA1c | 8.94 | 8.77 | 1.18 |
| Insulin Use | 0.30 | 0.00 | 0.30 |

The synthetic population has an age of 54.25 versus 59.97 in the real cohort.
The BMI is 29.76 synthetic versus 24.27 real.
HbA1c levels are 8.77 synthetic versus 8.94 real.
The real dataset shows 0.30 insulin use, whereas the synthetic dataset subset used has 0.00.

## Glucose Dynamics
| Metric | Real (ShanghaiT2DM) | Synthetic (DiaTwin) | Wasserstein Distance |
| :--- | :--- | :--- | :--- |
| Mean Glucose | 150.02 | 216.31 | 66.29 |
| Glucose Std | 41.38 | 44.53 | 3.67 |
| Glucose CV | 0.28 | 0.21 | 0.07 |
| Time Below 70 | 0.007 | 0.009 | 0.002 |
| Time 70-180 | 0.770 | 0.313 | 0.458 |
| Time Above 180 | 0.222 | 0.653 | 0.431 |
| Label Prevalence | 0.127 | 0.000 | - |
| Mean Gap Length | 67.50 | 5.00 | 62.50 |
| Meal Rise (2h) | not computable on real data (timestamps not provided for meals) | not computable on real data (timestamps not provided for meals) | - |

The synthetic dataset has a mean glucose of 216.31 versus 150.02 real.
Standard deviation is 44.53 synthetic versus 41.38 real.
Coefficient of variation is 0.21 synthetic versus 0.28 real.
Time below 70 is 0.009 synthetic versus 0.007 real.
Time in range (70-180) is 0.313 synthetic versus 0.770 real.
Time above 180 is 0.653 synthetic versus 0.222 real.
Mean gap length is 5.00 minutes synthetic versus 67.50 minutes real.
Label prevalence is 0.000 synthetic versus 0.127 real.

## Generator Improvement Recommendations
To match the real data better, a new synthetic cohort would need to change:
- Target a lower mean glucose level around 150 (currently 216) for typical T2D patients in this cohort.
- Increase the time in range (70-180) from 0.31 to 0.77 and reduce the time above 180 from 0.65 to 0.22.
- Introduce realistic sensor missingness and longer gap lengths (average gap length of 67.5 minutes instead of 5 minutes).
- Include insulin-using patient phenotypes to match the 0.30 real population prevalence.
