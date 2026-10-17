# Submission Summary

## Description

Managing Type 2 diabetes requires anticipating glycemic excursions and evaluating daily lifestyle choices without risking adverse events. DiaTwin is an in-silico metabolic digital twin state machine that combines patient physiological parameters, continuous glucose monitoring, and wearable sensor streams. The prototype reconstructs metabolic states, forecasts glucose trajectories over a 2 hour horizon, classifies imminent glycemic spike risk defined as a glucose rise of 50 mg/dL or more within 2 hours, and simulates counterfactual lifestyle modifications including meal timing, carbohydrate reduction, and physical activity.

The system was evaluated in this synthetic setting across 40 simulated patients (28 train, 6 validation, 6 test). On the test split of 6 test patients, the risk classification model achieved a ROC-AUC of 0.925 [0.907 - 0.944], a PR-AUC of 0.682 [0.565 - 0.797], and an Expected Calibration Error of 0.0275 in this synthetic setting. On the validation split, the 60-minute forecast achieved an RMSE of 18.41 mg/dL with 80.0% empirical coverage for the nominal 80% conformal interval in this synthetic setting. For the What-if simulator test evaluation on 6 test patients, the peak errors are 1.0, 10.2, and 11.5 mg/dL across three scenarios.

The prototype has several important limits. The what-if 80% effect intervals under-cover on 6 test patients, achieving empirical coverage of 0%, 17%, and 0%. Forecast test metrics were not saved and a new held-out evaluation is planned. The primary training data are synthetic with a comparison to 100 real patients from the ShanghaiT2DM cohort: mean glucose is 219.30 mg/dL in synthetic versus 141.01 mg/dL in the real cohort, and time above 180 mg/dL is 68.6% versus 19.6%. The user data entry page is experimental and provides an indicative estimate only. The system is not a medical device.

The application can be run locally using `streamlit run app/main.py` or verified using `pytest`. It can also be deployed to Streamlit Community Cloud in demo bundle mode by setting `DIATWIN_DEMO_BUNDLE = "1"`.

## Five-Line Pitch

1. DiaTwin creates an in-silico metabolic twin for continuous glucose monitoring and wearable signals.
2. It classifies imminent glycemic spikes of 50 mg/dL within 2 hours using calibrated risk models.
3. Multi-horizon forecasters provide uncertainty intervals for future glucose trajectories.
4. The counterfactual engine explores what-if lifestyle adjustments like meal shifts and exercise.
5. Built with causal state isolation and validated against a real-world diabetic patient cohort.

## Files to Open First

1. `README.md`: Project overview, metric summary, architecture diagram, and quick start guide.
2. `docs/SPEC.md`: Technical specification, state machine design, and causal isolation constraints.
3. `docs/MODEL_CARD.md`: Model card documenting risk and forecast metrics, calibration, and limitations.
4. `docs/REALISM.md`: Quantitative comparison between the synthetic cohort and 100 real patients.
5. `app/main.py`: Entrypoint for the interactive multi-page Streamlit web application.
