# Submission Summary

**Title**: DiaTwin: A Digital Twin for Glucose Forecasting and Counterfactual Simulation

**Short Description**: An in-silico research prototype that combines a digital twin state machine, calibrated risk forecasting (XGBoost), and a what-if simulation engine to predict glucose trajectories and test lifestyle interventions.

**Core Innovation**:
DiaTwin enforces a strict causal separation between historical state reconstruction (the twin) and probabilistic future forecasting. By freezing the calibrated risk model before exposing it to the simulation engine, we guarantee that all what-if scenarios are evaluated without look-ahead bias.

**Key Technical Details**:
- **Data Source**: Fully synthetic, continuous data (CGM, HR, Activity, Sleep) generated for 40 hypothetical patient profiles over a 10-day period.
- **Model**: XGBoost trained with Pinball Loss, calibrated post-hoc using Conformal Quantile Regression to provide 80% coverage intervals.
- **Architecture**: A digital twin registry that fuses static EHR features with a rolling 36-hour context window of streaming data.
- **Integrity Protocol**: A cryptographic hash-based freeze system prevents the simulation engine from altering the base model, ensuring test set validity.

**Top 5 Limitations**:
1. The physiological data generation relies on simplified random-walk and sinusoidal heuristics; it does not accurately reflect real-world metabolic complexity.
2. The dataset is small (40 synthetic patients) and lacks meaningful demographic or comorbidity diversity.
3. The What-if Simulator uses the same model family for generating baseline and counterfactual states, which might mask unmodeled physiological interactions.
4. The prototype does not currently model medication adherence, insulin absorption dynamics, or long-term complications.
5. The model relies on an arbitrary "spike" classification threshold that has not been evaluated in human clinical studies against specific patient risk profiles.

**Deployment**:
The Streamlit dashboard runs in an offline demo mode powered by a precomputed artifact bundle, minimizing live computational overhead while ensuring exact reproducibility.
