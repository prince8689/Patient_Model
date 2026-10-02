# Demo Run Sheet

**Target Length**: Under 3 minutes.
**Environment**: Local demo bundle mode (`DIATWIN_DEMO_BUNDLE=1`).

## Preparation
1. Ensure the app is running: `DIATWIN_DEMO_BUNDLE=1 streamlit run app/main.py`.
2. Open the app in a browser at 1920x1080 resolution, 100% zoom.
3. Start recording.

## Sequence

### 1. Patient List (0:00 - 0:20)
* **Action**: Navigate to "Patient List" in the sidebar.
* **Visual**: The cohort of 6 synthetic demo patients is displayed.
* **Action**: Click "Select" on patient **P040**.
* **Visual**: The app transitions to the Live Twin page for P040.

### 2. Live Twin & Drivers (0:20 - 1:00)
* **Action**: View the Live Twin page for **P040** at the default time (2026-01-03 22:20:00).
* **Visual**: 
  * The main KPIs show current glucose is 262.8 mg/dL and rising.
  * The Risk Band is **High** (Alert visible).
  * The forecast chart displays the rising trajectory and the 80% conformal uncertainty bands peaking around 348 mg/dL.
* **Action**: Scroll down to the "Top Risk Drivers" section.
* **Visual**: Three plain-language drivers are visible, explaining that the risk is driven by a recent large meal (73.3g carbs) that is still being absorbed.

### 3. What-if Simulator (1:00 - 1:45)
* **Action**: Navigate to "What-if Simulator" in the sidebar.
* **Visual**: Simulator interface opens for P040.
* **Action**: In the preset dropdown, select the **"typical breakfast preset"** (or manually input +15 min, 50g carbs). Check the boxes for three interventions (e.g., "walk_30min_moderate"). Click "Run Simulation".
* **Visual**: The chart updates to show the counterfactual trajectories. The model demonstrates how the 30-minute walk blunts the glucose peak compared to the baseline. Mention if one scenario shows wide uncertainty (low confidence).

### 4. Model Insights (1:45 - 2:20)
* **Action**: Navigate to "Model Insights" in the sidebar.
* **Visual**: The performance dashboard loads from the static bundle.
* **Action**: Click on the **"Integrity"** tab.
* **Visual**: Shows the cryptographic hashes matching the `FROZEN.json` manifest, proving no look-ahead leakage.
* **Action**: Click on the **"Limitations"** tab.
* **Visual**: The explicit limitations of the synthetic model are visible on screen.

### 5. About Page (2:20 - 2:45)
* **Action**: Navigate to "About" in the sidebar.
* **Visual**: The project overview and architecture diagram are displayed.
* **Action**: Scroll to the **"Challenge Mapping"** section.
* **Visual**: The table showing how the repository fulfills all requirements is visible.

### 6. Outro (2:45 - 3:00)
* **Action**: Scroll back to the top of the About page, highlighting the medical disclaimer.
* **End Recording.**
