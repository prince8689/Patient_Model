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
- **Alert Burden (Medium)**: 9.55 alerts/day
- **Alert Burden (Rule Baseline)**: 5.31 alerts/day
- **Event-Level Recall**: 83.51% (Medium), vs 23.37% (Rule Baseline)
- **Median Lead Time**: 65 minutes

## Subgroup Performance
- **Sex: Male**: AUC=0.956, Recall=0.929 (n=2)
- **Sex: Female**: AUC=0.910, Recall=0.899 (n=4)
- **Age: >= 55**: AUC=0.938, Recall=0.900 (n=3)
- **Age: < 55**: AUC=0.920, Recall=0.939 (n=3)
- **Error Types**: Total FN: 438, Total FP: 6714

## Limitations
- Built entirely on synthetic data.
- Tested on very small sample sizes.
- No real-world validation; no regulatory clearance.

## Reproducibility
- Seed: 42
- Commit Hash: e1e5a8166df39ec61d04cda05680b8000e500256
