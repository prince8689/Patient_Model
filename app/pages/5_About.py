import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pandas as pd
import streamlit as st

from app.components import disclaimer_banner
from src.app_lib.data_access import get_config
from src.app_lib.insights_vm import challenge_mapping, glossary, guided_demo_steps, limitations_list

st.set_page_config(layout="wide")
disclaimer_banner()

config = get_config()

st.title("About DiaTwin")
st.subheader("Educational prototype with synthetic data")
st.write("**One-sentence pitch**: DiaTwin is a proof-of-concept digital twin that fuses EHR and wearable data to predict and simulate glucose dynamics for patients with Type 2 Diabetes.")

st.header("1. The Problem")
st.write("Diabetes management relies heavily on patient self-regulation and retroactive clinician review. Patients often struggle to connect lifestyle choices to future glucose outcomes, leading to sub-optimal control. A proactive digital twin can bridge this gap by simulating future states and providing actionable foresight.")

st.header("2. What DiaTwin Does")
st.write("- **Fusion**: Combines static EHR profiles with continuous wearable and CGM data.")
st.write("- **Risk prediction**: Predicts likelihood of hyper/hypoglycemic spikes in the next 2 hours, with explanations.")
st.write("- **Forecast**: Provides a 2-hour glucose trajectory with conformal uncertainty bands.")
st.write("- **What-if Simulation**: Allows users to test hypothetical lifestyle interventions.")
st.write("- **Data Quality**: Honestly reports missing or stale data, adjusting confidence accordingly.")
st.write("- **Alerts**: Generates smart, rate-limited clinical alerts.")

st.header("3. Architecture & Data Flow")
st.markdown("`Synthetic EHR + wearable -> Features -> Frozen Model -> Twin State -> Forecast -> What-If -> Dashboard`")

st.header("4. Data")
st.write("DiaTwin operates entirely on **synthetic data** generated specifically for this challenge. This ensures patient privacy and provides absolute ground truth for evaluation. We use a **patient-wise split**, meaning a patient's data only exists in one split (train, val, or test).")
st.markdown("[Read the full Data Card](docs/DATA_CARD.md)")

st.header("5. Safety and Integrity")
st.write("- **Frozen-before-test protocol**: Models and thresholds are locked before any test set evaluation.")
st.write("- **No leakage guards**: The UI and view-model strictly prevent access to oracle or future data.")
st.write("- **Patient-level Confidence**: Metrics are evaluated per-patient to highlight variability.")
st.write("- **Calibration and Conformal Prediction**: Probabilities are calibrated and forecasts include verified uncertainty bands.")
st.write("- **Safety Scope**: Explicitly excludes insulin and medication modeling.")

st.header("6. Limitations")
for lim in limitations_list():
    st.write(f"- {lim}")

st.header("7. Challenge Mapping")
st.table(pd.DataFrame(challenge_mapping()))

st.header("8. Guided Demo")
for step in guided_demo_steps():
    st.write(f"**Step {step['step']}**: Go to [{step['page']}] - {step['patient_rule']}")
    st.caption(f"Look at: {step['look_at']}")

st.header("9. Glossary")
for term in glossary():
    with st.expander(term["term"]):
        st.write(term["definition"])

st.header("10. Team and Links")
team_name = config["app"].get("team_name")
if not team_name:
    st.write("To be added by the team")
else:
    st.write(f"**Team**: {team_name}")
    st.write("**Members**:")
    for member in config["app"].get("team_members", []):
        st.write(f"- {member.get('name')} ({member.get('role')})")
    st.write(f"**Repo**: {config['app'].get('repo_url', 'N/A')}")

st.header("11. Downloads")
col1, col2, col3 = st.columns(3)
with col1:
    if os.path.exists("docs/MODEL_CARD.md"):
        with open("docs/MODEL_CARD.md", "r") as f:
            st.download_button("Download Model Card", f.read(), file_name="MODEL_CARD.md")
with col2:
    if os.path.exists("docs/DATA_CARD.md"):
        with open("docs/DATA_CARD.md", "r") as f:
            st.download_button("Download Data Card", f.read(), file_name="DATA_CARD.md")
with col3:
    if os.path.exists("reports/insights_bundle.json"):
        with open("reports/insights_bundle.json", "r") as f:
            st.download_button("Download Insights Bundle", f.read(), file_name="insights_bundle.json")

st.header("11. Credits and License")
if os.path.exists("LICENSE"):
    with open("LICENSE", "r") as f:
        st.text(f.read())
else:
    st.text("Copyright (c) 2026 DiaTwin contributors\n\nMIT License...")
