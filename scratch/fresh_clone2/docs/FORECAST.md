# Forecast Module

## Architecture
The DiaTwin forecast module predicts patient glucose trajectories for the next 120 minutes in 5-minute intervals. It is designed to provide , probabilistic forecasts of future states using Conformal Quantile Regression (CQR).

### 1. Baselines
We evaluate against three baselines to justify the complexity of learning models:
- **Persistence:** Predicts that future glucose will be identical to current glucose (delta = 0).
- **Linear Extrapolation:** Multiplies the recent 30-minute slope by a tuned damping factor.
- **Ridge Regression:** A simple linear combination of all features.

### 2. Quantile XGBoost
The primary model is an XGBoost model trained with the Pinball Loss objective (`reg:quantileerror`) at quantiles 0.1, 0.5, and 0.9.
- **Tuning:** Hyperparameters are tuned on the 60-minute median horizon using GroupKFold cross-validation over the `train` split.
- **Non-Crossing Constraint:** Quantile crossing is fixed using simple rearrangement (sorting) post-prediction.

### 3. Conformal Calibration
To achieve the nominal 80% coverage interval, we calibrate the outputs on the `val` split using Conformal Quantile Regression (CQR) scores. A single scalar $q$ per horizon is added/subtracted to the 0.9/0.1 quantiles respectively.

### 4. Interpolation
The model outputs discrete horizons (15, 30, 60, 90, 120m). We use monotone Piecewise Cubic Hermite Interpolating Polynomial (PCHIP) interpolation to infer the trajectory at 5-minute increments between horizons, preserving monotonicity and preventing artificial spikes.

### 5. Spike Consistency
The twin engine verifies that the forecast trajectory is probabilistically consistent with the frozen classification model. Discrepancies are flagged in the forecast result object.

## Evaluation
Test evaluation is guarded by a freeze step (`models/FORECAST_FROZEN.json`). Metrics include MAE, RMSE, Coverage (Calibrated and Uncalibrated), and Clarke Error Grid.
