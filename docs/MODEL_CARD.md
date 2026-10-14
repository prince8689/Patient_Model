# DiaTwin Model Card (v1.0)

## Model Details
- **Type**: XGBoost Classifier
- **Version**: v1.0
- **Features**: 75 engineered time-series and static features covering Glucose, Meals, Activity, Heart Rate, Sleep, Time, EHR, Personal Baseline, and Missingness.
- **Training Data**: Synthetic tabular dataset (simulating EHR + Wearable signals) representing ~28 patients in the training set.

## Intended Use
- **Primary Use**: Predicting glucose spikes (increase of >= 50 mg/dL) up to 2 hours in advance in Type 2 Diabetes patients.
- **Target Audience**: Healthcare providers testing interventions in a simulated "what-if" environment.

## Out-of-Scope Use
- Not for clinical deployment or real-world diagnostics.
- Not for Type 1 Diabetes management or automated insulin delivery.

## Data
- **Source**: 100% synthetically generated.
- **Splits**: Strict patient-wise stratification (Train 70% / Val 15% / Test 15%).

## Metrics (Test Set)
- **Prevalence**: 14.76%
- **ROC-AUC**: 0.925 (95% CI: 0.907-0.944)
- **PR-AUC**: 0.682 (95% CI: 0.565-0.797)
- **Brier Score**: 0.0737
- **Log Loss**: 0.2384
- **ECE**: 0.0275

## Calibration
- **Method**: Isotonic Regression fitted on Out-of-Fold training predictions.
- **Result**: Probabilities map closely to empirical event rates.

## Thresholds and Risk Bands
- **Low Risk**: < 0.1538
- **Medium Risk**: [0.1538, 0.3158)
- **High Risk**: >= 0.3158

## Explainability
- **Method**: SHAP (TreeExplainer)
- **Top Drivers**: 
  1. glu_current
  2. meal_carbs_last_60m
  3. glu_delta_30m
  4. meal_min_since_last

## Clinical-Utility Results
Clinical utility metrics such as alert burden and event-level recall are detailed in evaluation reports.

## Subgroup Performance
Subgroup performance analyses by demographic factors are evaluated in retrospective cohort reports.
Confusion matrix error counts for the medium risk threshold (from `reports/metrics_test_day7.json`): False Negatives = 438, False Positives = 6714.

## Limitations
- Built entirely on synthetic data.
- The model is for Type 2 diabetes and predicts a glucose rise of 50 mg/dL or more within 2 hours.
- Tested on very small sample sizes (40 synthetic patients, 6 test patients).
- No real-world validation; no regulatory clearance.
- For the What-if Simulator test evaluation (6 test patients), the peak error is 1.0, 10.2 and 11.5 mg/dL for the three tested scenarios (reports/WHATIF_TEST_DONE.json). The 80% interval coverage is 0%, 17% and 0%. The uncertainty bands significantly under-cover.
- Forecast test metrics were not saved and a new held-out evaluation is planned.
- The synthetic data differ from the real cohort in glucose level: mean glucose is 219.30 mg/dL in synthetic vs 141.01 mg/dL in the real cohort; time above 180 is 68.6% in synthetic vs 19.6% in the real cohort (from reports/realism_comparison.json).
- Integrity record: the risk model freeze precedes its test evaluation in git history; for the forecast and what-if modules the manifest and the test marker were committed together so freeze-before-test cannot be shown from git.

## Reproducibility
- Seed: 42
- Commit Hash: e1e5a8166df39ec61d04cda05680b8000e500256
