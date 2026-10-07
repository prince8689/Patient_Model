import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import time

import pandas as pd
import streamlit as st

from app.components import (
    disclaimer_banner,
    kpi_card,
    render_band_badge,
    render_status_badge,
)
from src.app_lib.figures import glucose_forecast_figure, risk_strip_figure
from src.app_lib.moments import (
    available_moments,
    default_moment,
    next_alert,
    previous_meal,
    step_time,
)
from src.app_lib.viewmodels import export_state_json, twin_view

st.set_page_config(layout="wide")
disclaimer_banner()

if "patient_id" not in st.session_state:
    st.warning("Please select a patient from the Patient List.")
    st.stop()
    
pid = st.session_state["patient_id"]
moms = available_moments(pid)

if not moms:
    st.error("No valid moments found for this patient.")
    st.stop()

if "as_of" not in st.session_state or st.session_state["as_of"] is None:
    st.session_state["as_of"] = default_moment(pid)

current = st.session_state["as_of"]
if current not in moms:
    current = min(moms, key=lambda x: abs(x - current))
    st.session_state["as_of"] = current

# Controls
st.sidebar.header("Time Controls")
st.sidebar.write(f"As of: {current.strftime('%Y-%m-%d %H:%M')}")

def set_time(new_t):
    st.session_state["as_of"] = new_t

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("-1h"): set_time(step_time(pid, current, -60))
    if st.button("-5m"): set_time(step_time(pid, current, -5))
with col2:
    if st.button("+5m"): set_time(step_time(pid, current, 5))
    if st.button("+1h"): set_time(step_time(pid, current, 60))
    
if st.sidebar.button("Previous Meal"):
    set_time(previous_meal(pid, current))
if st.sidebar.button("Next Alert"):
    set_time(next_alert(pid, current))
if st.sidebar.button("Reset Default"):
    set_time(default_moment(pid))
    
st.sidebar.markdown("---")
# Replay fragment
@st.fragment(run_every=2)
def replay_fragment():
    if st.session_state.get("is_playing", False):
        new_t = step_time(pid, st.session_state["as_of"], 5)
        if new_t > st.session_state["as_of"]:
            st.session_state["as_of"] = new_t
            st.rerun()
        else:
            st.session_state["is_playing"] = False
            
    if st.button("Stop" if st.session_state.get("is_playing") else "Play"):
        st.session_state["is_playing"] = not st.session_state.get("is_playing", False)
        st.rerun()

replay_fragment()

st.sidebar.markdown("---")
overlay = st.sidebar.checkbox("Show actual future glucose (evaluation only)")

# Load view
start_t = time.time()
view = twin_view(pid, current, include_actual_overlay=overlay)
render_t = time.time() - start_t
st.sidebar.caption(f"Render time: {render_t:.2f}s")

# Header
st.title(f"Twin: {pid}")
prof = view["profile"]
st.write(f"{prof['age']} yo {prof['sex']} | BMI: {prof['bmi']} | HbA1c: {prof['hba1c']} | Duration: {prof['diabetes_duration_years']}y")
st.markdown(render_status_badge(view["data_quality"]["status"]), unsafe_allow_html=True)

if view["data_quality"]["status"] == "warming_up":
    st.warning("Twin is warming up. Not enough data for prediction.")
elif view["data_quality"]["status"] == "stale":
    st.error("Stale data. Twin predictions suspended.")

# KPIs
c1, c2, c3, c4 = st.columns(4)
kpis = view["kpis"]
with c1:
    v = f"{kpis['current_glucose']:.0f} {kpis['trend_direction']}" if kpis['current_glucose'] else "N/A"
    sv = f"30m change: {kpis['trend_30m']:.0f}" if kpis['trend_30m'] else None
    kpi_card("Glucose", v, sv)
with c2:
    v = render_band_badge(kpis['band'])
    sv = f"Prob: {kpis['probability']:.0%}" if kpis['probability'] else None
    st.markdown(f"**Risk**<br>{v}", unsafe_allow_html=True)
    if sv: st.caption(sv)
with c3:
    if kpis['predicted_peak']:
        v = f"{kpis['predicted_peak']:.0f} mg/dL"
        sv = f"in {kpis['predicted_peak_minutes']} mins"
        if kpis['hypo_risk']: sv += " (Hypo risk)"
        if kpis['hyper_risk']: sv += " (Hyper risk)"
    else:
        v = "N/A"
        sv = None
    kpi_card("Predicted Peak", v, sv)
with c4:
    v = f"{kpis['tir_24h']:.0f}%" if pd.notna(kpis['tir_24h']) else "N/A"
    kpi_card("TIR 24h", v)

st.markdown("---")

col_main, col_side = st.columns([2, 1])

with col_main:
    st.subheader("Glucose Forecast")
    fig = glucose_forecast_figure(view)
    st.plotly_chart(fig, use_container_width=True)
    st.info(view["forecast_summary"])
    
    st.subheader("Risk History")
    fig_risk = risk_strip_figure(view)
    st.plotly_chart(fig_risk, use_container_width=True)

with col_side:
    st.subheader("Why this risk")
    if view["drivers"]:
        for d in view["drivers"]:
            icon = "🔼" if d["contribution"] > 0 else "🔽"
            st.markdown(f"{icon} **{d['name']}**: {d['value']:.1f}")
            st.progress(min(abs(d["contribution"]), 1.0))
        st.page_link("pages/4_Model_Insights.py", label="Learn more about drivers", icon="🔍")
    else:
        st.write("No drivers available.")
        
    st.subheader("Context")
    ctx = view["context"]
    st.write(f"Meals: {ctx['minutes_since_last_meal']} mins ago, {ctx['carbs_on_board_estimate']:.0f}g COB")
    st.write(f"Activity: {ctx['minutes_since_last_activity']} mins ago")
    st.write(f"Sleep: {ctx['sleep_state']}")
    
    st.subheader("Recent Alerts")
    if view["alerts_48h"]:
        for a in view["alerts_48h"][:5]:
            st.markdown(f"*{a['timestamp'][11:16]}* - " + render_band_badge(a['band']), unsafe_allow_html=True)
    else:
        st.write("No recent alerts.")
        
st.download_button("Download Twin State (JSON)", data=export_state_json(pid, current), file_name=f"twin_{pid}.json")

if st.button("Try a what-if at this moment"):
    st.switch_page("pages/3_What_If_Simulator.py")
