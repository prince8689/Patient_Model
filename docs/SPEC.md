# DiaTwin: Digital Twin Specification

## 1. Problem Statement
Type 2 Diabetes management today is largely reactive, relying on point-in-time checks or threshold-based alerts that warn patients only after their glucose has already reached unsafe levels. This approach leaves patients adjusting to physiological stress rather than preventing it, increasing the risk of long-term complications and reducing quality of life.

A proactive digital twin, DiaTwin, shifts the paradigm from reactive monitoring to predictive simulation. By fusing real-time wearable data with static Electronic Health Records (EHR), DiaTwin creates a continuous, dynamic replica of the patient's metabolic state. This allows healthcare providers and patients to forecast glucose spikes before they occur and simulate interventions safely in a virtual environment.

## 2. Solution Overview
DiaTwin is a proof-of-concept Digital Twin tailored for Type 2 Diabetes patients. It ingests continuous data streams (CGM, heart rate, sleep, physical activity) and baseline clinical profiles (EHR). Using an XGBoost-based prediction engine, it forecasts the likelihood of a significant glucose spike (>= 50 mg/dL rise) within the next two hours. A built-in "what-if" simulator allows doctors to modify upcoming events—such as adjusting meal times, changing carbohydrate intake, or adding exercise—to instantly visualize the simulated impact on the patient's future glucose trajectory, all presented in an interactive Streamlit dashboard.

## 3. Architecture
The architecture comprises six key layers: Data Layer, Feature Engineering, Prediction Model, Twin State Engine, What-if Simulator, and Streamlit Dashboard.

```mermaid
flowchart TD
    A[Data Layer (EHR & Wearables)] --> B[Feature Engineering]
    B --> C[Prediction Model (XGBoost)]
    B --> D[Twin State Engine]
    C --> D
    D --> E[What-if Simulator]
    D --> F[Streamlit Dashboard]
    E --> F
```

## 4. Data Schema
The system uses two primary synthetic datasets:

**`patients.csv`**
- `patient_id` (str): Unique identifier for the patient.
- `age` (int): Patient's age in years.
- `sex` (str): M/F.
- `bmi` (float): Body Mass Index.
- `hba1c` (float, %): Average blood sugar levels over the past 3 months.
- `diabetes_duration_years` (float): Years since diagnosis.
- `on_insulin` (int): 0 or 1, indicating if the patient takes insulin.
- `on_metformin` (int): 0 or 1, indicating if the patient takes metformin.
- `baseline_insulin_sensitivity` (float): Hidden parameter for simulation variance.

**`wearable.csv` (5-minute intervals)**
- `patient_id` (str): Matches `patients.csv`.
- `timestamp` (datetime): Time of the reading.
- `glucose_mgdl` (float): Continuous Glucose Monitor reading.
- `heart_rate` (float): Beats per minute.
- `steps` (int): Steps taken in the 5-minute interval.
- `sleep_state` (str): awake/light/deep/rem.
- `meal_carbs_g` (float): Carbohydrates consumed (0 when no meal).
- `activity_intensity` (int): Scale of 0-3.

## 5. Prediction Target
The primary predictive target is `spike_next_2h`.
- **Definition:** `spike_next_2h = 1` if the maximum `glucose_mgdl` in the next 120 minutes is `>=` current `glucose_mgdl` + 50 mg/dL, else `0`.
- **Data Leakage Prevention:** Feature engineering will strictly use a sliding window looking back (e.g., 120 minutes of history). Future timestamps will only be used to compute the target label during training and will be completely excluded from the feature matrix used for predictions.

## 6. Synthetic Data Realism Requirements
To ensure the proof-of-concept is medically plausible, the synthetic data generator must adhere to the following rules:
- **Meal-driven glucose curves:** Meals should induce a rapid glucose rise followed by an insulin-mediated decay.
- **Dawn phenomenon:** Early morning (e.g., 4 AM - 8 AM) should exhibit a natural glucose elevation.
- **Exercise effects:** Moderate to high activity intensity should generally lower glucose levels and elevate heart rate.
- **Sleep cycles:** Heart rate should naturally dip during deep/REM sleep phases.
- **Patient variation:** Curves and baselines should vary across patients, driven primarily by the `baseline_insulin_sensitivity` parameter.
- **Sensor noise and missingness:** Add Gaussian noise to CGM readings and simulate random data dropouts (small percentage) to reflect real-world hardware imperfections.

## 7. Modeling Plan
- **Baseline Model:** Logistic Regression to establish a performance floor.
- **Main Model:** XGBoost to capture non-linear metabolic interactions.
- **Data Splitting:** PATIENT-WISE train/validation/test split (e.g., 70/15/15) to ensure no patient overlaps across splits, proving the model generalizes to new individuals.
- **Class Imbalance:** Will handle utilizing class weight adjustments (e.g., `scale_pos_weight` in XGBoost) or SMOTE if necessary.

## 8. Evaluation Metrics
- **ROC-AUC:** Primary metric for overall discrimination capability.
- **PR-AUC:** Key metric due to the likely class imbalance of "spike" events.
- **Recall at Fixed Precision:** Ensure high sensitivity for clinical safety without overwhelming the user with false positives.
- **Calibration Curve:** To assess if predicted probabilities map well to true spike frequencies.
- **Explainability:** SHAP feature importance to provide clinical interpretability for every prediction.

## 9. Twin State Definition
The "Twin State" is the in-memory representation of a patient at a specific timestamp. It includes:
- **Patient Profile:** Static EHR attributes.
- **Latest Measurements:** Recent history of wearable data (last 120 mins).
- **Current Risk Score:** Probability of a spike (0-100%).
- **Risk Band:** Categorized as Low, Medium, or High.
- **Top 3 Risk Drivers:** Extracted from local SHAP values (e.g., "High Carb Intake").
- **2-Hour Forecast:** The simulated glucose trajectory for the next 120 minutes.

## 10. What-if Simulator Scope
The simulator allows the provider to test hypothetical interventions:
- **Walk 10 min:** Adds a 10-minute period of moderate activity (`activity_intensity` = 2) starting from the current time.
- **Eat 30 min earlier:** Shifts the timing of the next planned meal back by 30 minutes.
- **Reduce meal carbs by 30%:** Decreases the `meal_carbs_g` of the upcoming meal by 30%.
- **Estimation mechanism:** The model is re-run with the altered future features to generate a new simulated glucose trajectory and a revised `spike_next_2h` probability.

## 11. Dashboard Views (Streamlit)
- **Patient List:** A triage view sorting patients by current risk score.
- **Live Twin:** The main detailed view for a single patient showing real-time charts and current Twin State.
- **What-if Simulator:** Interactive form to select interventions and overlay the simulated outcome on the current trajectory.
- **Model Insights:** Global SHAP importance, evaluation metrics, and feature distributions.
- **About:** Overview of the methodology and project details.

## 12. Ethics and Limitations
- **Data:** All data is entirely synthetic.
- **Clinical Validity:** This is an educational and technical proof-of-concept, NOT a medical device. It has not been clinically validated.
- **Simulations:** Simulator effects are based on heuristic assumptions encoded in the synthetic data generator and learned by the model, not verified physiological models.

## 13. Assumptions List
- **Timezone:** Assumed all timestamps are local to the patient.
- **Sampling rate:** 5 minutes is strictly enforced with forward-filling for missingness during feature engineering.
- **Missing values:** Small gaps (<30 mins) will be interpolated, larger gaps will trigger a "Data Quality Alert" in the Twin State.
- **What-if execution:** The simulator assumes we know the user's intended near-future actions (e.g., they log an upcoming meal).
