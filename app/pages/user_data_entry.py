import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app_lib.data_access import get_config, get_registry
from src.app_lib.user_input import (
    load_user_config, validate_profile, validate_glucose, 
    validate_meals_exercise, build_frame, evaluate_tier,
    run_indicative_path, run_full_path, get_provided_summary,
    get_sensitivity_statement, get_confidence_label
)

st.set_page_config(page_title="Your Data (experimental, indicative estimate)", layout="wide")

st.title("Personalized Forecast (experimental, indicative estimate)")

st.warning("Educational prototype trained on synthetic data only. Not validated on real people. Not a medical device. Not for treatment decisions.")
st.info("**Notice**: This page provides an **experimental, indicative estimate**. Sleep, heart rate and steps are filled with fixed placeholders when the user gives none (the sleep state 'unknown' makes the history look like sleep in the features), history features are replaced by training medians, and the confidence is never 'high' unless the full 24 hour history is provided.")
st.caption("Your entries are not stored. When this app is hosted, use fictional values only.")

registry = get_registry()
engine_config = get_config()

if not hasattr(registry, "pipeline") or registry.pipeline is None:
    try:
        from src.twin.loader import TwinRegistry
        registry = TwinRegistry(engine_config)
    except Exception:
        pass

if not hasattr(registry, "pipeline") or registry.pipeline is None:
    st.error("Available when run locally")
    st.code("python scripts/run_pipeline.py", language="bash")
    st.markdown("### Precomputed Example (Synthetic)")
    st.info("When run locally with models, you can enter custom data here.")
    st.stop()

u_config = load_user_config()

def clear_data():
    st.session_state.clear()

if st.button("Clear my data"):
    clear_data()
    st.rerun()

# ----------------- INPUTS -----------------
st.header("1. Your Profile")

col1, col2, col3, col4 = st.columns(4)
with col1:
    age = st.text_input("Age (18-90)", value=st.session_state.get("age", ""))
with col2:
    sex = st.selectbox("Sex", ["Female", "Male"], index=0 if st.session_state.get("sex", "Female") == "Female" else 1)
with col3:
    bmi = st.text_input("BMI (15-60)", value=st.session_state.get("bmi", ""))
with col4:
    hba1c = st.text_input("HbA1c % (4-15 or unknown)", value=st.session_state.get("hba1c", ""))
    
col5, col6, col7, col8 = st.columns(4)
with col5:
    dur = st.text_input("Diabetes Duration (yrs, unknown)", value=st.session_state.get("dur", ""))
with col6:
    ins = st.selectbox("On Insulin?", ["No", "Yes"], index=0 if st.session_state.get("ins", "No") == "No" else 1)
with col7:
    met = st.selectbox("On Metformin?", ["Yes", "No"], index=0 if st.session_state.get("met", "Yes") == "Yes" else 1)
with col8:
    hyp = st.selectbox("Hypertension?", ["No", "Yes"], index=0 if st.session_state.get("hyp", "No") == "No" else 1)

raw_profile = {
    "age": age, "sex": sex, "bmi": bmi, "hba1c": hba1c,
    "diabetes_duration_yrs": dur, "on_insulin": ins,
    "on_metformin": met, "hypertension": hyp
}

st.header("2. Current Time")
now_input = st.text_input("Now (YYYY-MM-DD HH:MM) or leave blank for local time", value=st.session_state.get("now_input", ""))
if not now_input:
    now = datetime.now().replace(second=0, microsecond=0)
else:
    try:
        now = pd.to_datetime(now_input).to_pydatetime()
    except Exception:
        st.error("Invalid time format. Using current local time.")
        now = datetime.now().replace(second=0, microsecond=0)

st.header("3. Glucose Readings")
st.write("Enter readings (Time can be 'HH:MM' or minutes before now like '-15'). At least one reading is required.")

if "gluc_data" not in st.session_state:
    st.session_state.gluc_data = pd.DataFrame([{"time": "-5", "value": "", "unit": "mg/dL"}])
    
gluc_df = st.data_editor(st.session_state.gluc_data, num_rows="dynamic", key="gluc_editor")

st.markdown("Or upload CSV (columns: time, value, unit)")
uploaded_csv = st.file_uploader("Upload CSV", type=["csv"])

st.header("4. Meals and Exercise")
col_m, col_e = st.columns(2)
with col_m:
    if "meal_data" not in st.session_state:
        st.session_state.meal_data = pd.DataFrame([{"time": "", "carbs": ""}])
    st.write("Meals (Carbs 0-200g)")
    meal_df = st.data_editor(st.session_state.meal_data, num_rows="dynamic", key="meal_editor")
with col_e:
    if "ex_data" not in st.session_state:
        st.session_state.ex_data = pd.DataFrame([{"time": "", "duration": "", "intensity": "light"}])
    st.write("Exercise (Duration 5-120m, light/moderate/vigorous)")
    ex_df = st.data_editor(st.session_state.ex_data, num_rows="dynamic", key="ex_editor")

st.header("5. Optional Sleep and Activity Context")
col_b, col_w, col_s = st.columns(3)
with col_b:
    bedtime_in = st.text_input("Usual bedtime (HH:MM or hour, optional)", value=st.session_state.get("bedtime_in", ""))
with col_w:
    waketime_in = st.text_input("Usual wake time (HH:MM or hour, optional)", value=st.session_state.get("waketime_in", ""))
with col_s:
    steps_1h_in = st.text_input("Steps in last hour (optional)", value=st.session_state.get("steps_1h_in", ""))

if st.button("Run Forecast"):
    st.session_state.age = age
    st.session_state.sex = sex
    st.session_state.bmi = bmi
    st.session_state.hba1c = hba1c
    st.session_state.dur = dur
    st.session_state.ins = ins
    st.session_state.met = met
    st.session_state.hyp = hyp
    st.session_state.now_input = now_input
    st.session_state.bedtime_in = bedtime_in
    st.session_state.waketime_in = waketime_in
    st.session_state.steps_1h_in = steps_1h_in
    
    # ---------------- VALIDATION ----------------
    valid_prof, err_p = validate_profile(raw_profile)
    
    raw_gluc = gluc_df.to_dict("records")
    if uploaded_csv is not None:
        try:
            csv_df = pd.read_csv(uploaded_csv)
            raw_gluc.extend(csv_df.to_dict("records"))
        except Exception:
            st.error("Failed to parse CSV.")
            
    raw_gluc = [r for r in raw_gluc if str(r.get("value", "")).strip() != ""]
    raw_meal = [r for r in meal_df.to_dict("records") if str(r.get("carbs", "")).strip() != ""]
    raw_ex = [r for r in ex_df.to_dict("records") if str(r.get("duration", "")).strip() != ""]
    
    valid_gluc, err_g = validate_glucose(raw_gluc, now)
    valid_meal, valid_ex, err_me = validate_meals_exercise(raw_meal, raw_ex, now)
    
    all_errs = err_p + err_g + err_me
    if all_errs:
        for e in all_errs:
            st.error(e)
        if not valid_gluc:
            st.stop()
            
    out_of_bounds = False
    if valid_prof["age"] < 18 or valid_prof["age"] > 90:
        out_of_bounds = True
    if valid_prof["bmi"] < 15 or valid_prof["bmi"] > 60:
        out_of_bounds = True
    
    if out_of_bounds or any(g["glucose_mgdl"] < 70 or g["glucose_mgdl"] > 250 for g in valid_gluc):
        st.warning("The estimate is outside what the model has seen in training (e.g. Age 18-90, BMI 15-60). Anyone who feels unwell or has very high or very low readings should contact a doctor or emergency services.")
        
    hist_hours = engine_config["twin"]["history_buffer_hours"]
    frame, adjustments = build_frame(
        valid_gluc, valid_meal, valid_ex, now, hist_hours,
        bedtime=bedtime_in, wake_time=waketime_in, steps_last_hour=steps_1h_in
    )
    
    for a in adjustments:
        st.info(a)
        
    tier, missing_groups = evaluate_tier(frame, now, u_config["data_sufficiency"])
    
    if tier == "invalid":
        st.error("Data rejected. A reading older than 20 minutes cannot be used for the indicative path without 24h history.")
        st.stop()
        
    # Execute Model
    with st.spinner("Simulating..."):
        if tier == "full":
            res = run_full_path(frame, valid_prof, engine_config, registry.pipeline, registry.calibrator, registry.forecast_artifacts, registry.thresholds, registry.explainer, registry.whatif_artifacts)
        else:
            res = run_indicative_path(frame, valid_prof, engine_config, registry.pipeline, registry.calibrator, registry.forecast_artifacts, registry.thresholds, registry.explainer)
            
        risk = res["risk"]
        fcst = res["forecast"]
            
    summary_info = get_provided_summary(valid_gluc, valid_meal, valid_ex, missing_groups)
    
    st.divider()
    st.warning("Educational prototype trained on synthetic data only. Not validated on real people. Not a medical device. Not for treatment decisions.")
    st.caption(summary_info["cohort_comparison"])
    
    if risk is None or fcst is None:
        st.error("Failed to generate forecast.")
        st.stop()
        
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Glucose", f"{frame['glucose_mgdl'].dropna().iloc[-1]:.0f} mg/dL")
    with col2:
        st.metric("Risk Band", risk.band, f"{risk.probability_calibrated:.1%} prob", delta_color="inverse" if risk.band == "High" else "off")
    with col3:
        st.metric("Predicted Peak", f"{fcst.predicted_peak:.0f} mg/dL", f"in {fcst.predicted_peak_minutes} min", delta_color="inverse")
    with col4:
        conf = get_confidence_label(tier, u_config["data_sufficiency"])
        st.metric("Data Confidence", conf, f"Tier: {tier}", delta_color="off")
        sensitivity_statement = get_sensitivity_statement(tier)
        st.caption(sensitivity_statement)
        
    # Chart
    fig = go.Figure()
    
    fig.add_hrect(y0=70, y1=180, fillcolor="green", opacity=0.1, line_width=0, name="Target Range")
    fig.add_hline(y=70, line_dash="dash", line_color="red", name="Hypo limit")
    fig.add_hline(y=180, line_dash="dash", line_color="orange", name="Hyper limit")
    
    past_df = frame.dropna(subset=["glucose_mgdl"])
    fig.add_trace(go.Scatter(x=past_df["timestamp"], y=past_df["glucose_mgdl"], mode="markers+lines", name="Observed", line=dict(color="blue")))
    
    times = pd.to_datetime(fcst.trajectory_5min["timestamp"])
    fig.add_trace(go.Scatter(
        x=times.tolist() + times.tolist()[::-1],
        y=fcst.trajectory_5min["upper"] + fcst.trajectory_5min["lower"][::-1],
        fill="toself", fillcolor="rgba(0,100,250,0.2)", line=dict(color="rgba(255,255,255,0)"), name="Uncertainty Band"
    ))
    fig.add_trace(go.Scatter(x=times, y=fcst.trajectory_5min["median"], mode="lines", name="Forecast Median", line=dict(color="blue", dash="dash")))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Drivers
    if risk.drivers:
        st.subheader("Top Risk Drivers")
        for d in risk.drivers:
            f_name = d.get("feature", d.get("feature_name", ""))
            desc = d.get("human_readable", d.get("description", ""))
            val = d.get("shap_value", d.get("impact", 0.0))
            st.write(f"- **{f_name}**: {desc} (SHAP value: {val:.3f})")
            
    st.subheader("What was and was not provided")
    st.info(summary_info["provided"])
    if missing_groups:
        st.warning(summary_info["not_provided"])
