# DiaTwin Demo Run Sheet

This script is for a 3 to 4 minute screen recording of the DiaTwin application running in demo-bundle mode.

**Prerequisites:**
- Run the app with `DIATWIN_DEMO_BUNDLE=1` via `demo_bundle.py` or `.env`.
- Ensure all demo bundle files are generated.

## Step 1: Patient List (0:00 - 0:30)
1. Navigate to the **Patient List** page.
2. Observe the overview of the 6 demo patients.
3. Highlight patient **P007**.
4. Click the link/button to view the **Live Twin** for **P007**.

## Step 2: Live Twin and Forecast (0:30 - 1:30)
1. On the **Live Twin** page, verify the timestamp is **2026-01-03 21:50**.
2. Point out that the patient currently has a **High** risk band and their glucose is rising after a recent meal.
3. Scroll down to the **Glucose Forecast** section.
4. Highlight the predicted peak and the uncertainty bands.
5. Emphasize the educational disclaimer clearly visible at the bottom or top of the page.

## Step 3: Drivers and Explanations (1:30 - 2:00)
1. Scroll to the **Risk Drivers** section on the same page.
2. Explain the top three drivers contributing to the High risk score: Time since last meal (`meal_min_since_last`), Carbs on board (`meal_cob_estimate`), and HbA1c (`ehr_hba1c`).
3. Briefly mention how this helps in understanding the underlying causes of the spike.

## Step 4: What-If Simulator (2:00 - 3:15)
1. Navigate to the **What-If Simulator** page.
2. Select patient **P007** and ensure the timestamp is still **2026-01-03 21:50**.
3. In the "Simulate Scenarios" panel, select a scenario like **walk_30min_moderate** or **split_meal_60min**.
4. Click **Run Simulation**.
5. Observe the new predicted peak and compare it against the baseline trajectory.
6. Highlight the clear peak difference and how it could theoretically inform lifestyle adjustments (again pointing out the disclaimer).

## Step 5: Model Insights (3:15 - 4:00)
1. Navigate to the **Model Insights** page.
2. Briefly scroll through the global metrics and model performance across different archetypes.
3. Show the limitations tab to highlight the safety constraints and bounds of the model.
4. Conclude the demo.
