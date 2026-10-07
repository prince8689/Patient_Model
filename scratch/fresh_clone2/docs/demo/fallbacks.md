# Demo Recording Fallbacks

If the app fails or encounters an error during the live recording, follow these fallback steps to ensure you can still capture the required footage.

## 1. App Startup Fails
**Symptom**: `streamlit run app/main.py` crashes on startup.
**Action**: 
- Ensure you have set the environment variable correctly. In Windows PowerShell, use:
  ```powershell
  $env:DIATWIN_DEMO_BUNDLE="1"
  .\.venv\Scripts\streamlit run app/main.py
  ```
- If the environment variable isn't persisting, edit `configs/config.yaml` locally (do NOT commit this edit) and set `use_demo_bundle: true` under the `app:` section.

## 2. Missing Patient or Missing Data
**Symptom**: Clicking on P040 causes a "Data Not Found" or "Missing Forecast" error.
**Action**:
- The demo bundle is static. If P040 is corrupted on your local clone, select **P038** instead. P038 also has a High risk band with a recent meal and rising glucose at time 2026-01-03 22:35.

## 3. What-if Simulator Fails to Render
**Symptom**: The chart on the What-if page crashes.
**Action**:
- Ensure you have selected a preset. If presets fail, manually enter +15 offset and 50g carbs.
- Only select one intervention at a time if selecting three causes a layout overflow.

## 4. UI Elements Overlap or Cut Off
**Symptom**: Text is unreadable or clipped, particularly at 110% zoom.
**Action**:
- Resize your browser window horizontally to trigger Streamlit's responsive wrapping.
- Hide the Streamlit sidebar (click the 'X' or '<' arrow at the top left) to give the main content more horizontal space.

## 5. Integrity Tab is Blank
**Symptom**: The Model Insights -> Integrity tab shows no data.
**Action**:
- The `insights_bundle.json` might be malformed. Re-run `python scripts/build_insights_bundle.py` to regenerate it locally, then refresh the app.
