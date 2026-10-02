import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pandas as pd
import streamlit as st

from app.components import disclaimer_banner, render_band_badge, render_status_badge
from src.app_lib.figures import sparkline_figure
from src.app_lib.viewmodels import patient_overview

st.title("Patient List")
disclaimer_banner()
st.write("Demonstration of the DiaTwin engine on a subset of synthetic test patients.")
st.page_link("pages/5_About.py", label="Learn more about this dataset and prototype", icon="ℹ️")

@st.cache_data(ttl=60)
def get_overview():
    return patient_overview()

df = get_overview()

if df.empty:
    st.info("No demo patients found.")
    st.stop()

# Summary strip
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("High Risk", len(df[df["band"] == "High"]))
with col2:
    st.metric("Medium Risk", len(df[df["band"] == "Medium"]))
with col3:
    st.metric("Low Risk", len(df[df["band"] == "Low"]))
with col4:
    st.metric("Data Issues", len(df[df["data_status"] != "ok"]))

# Filters
col_f1, col_f2 = st.columns(2)
with col_f1:
    band_filter = st.selectbox("Filter by Risk Band", ["All", "High", "Medium", "Low"])
with col_f2:
    status_filter = st.selectbox("Filter by Data Status", ["All", "ok", "warming_up", "stale", "no_glucose", "low_completeness"])
    
filtered = df.copy()
if band_filter != "All":
    filtered = filtered[filtered["band"] == band_filter]
if status_filter != "All":
    filtered = filtered[filtered["data_status"] == status_filter]
    
# Render list
for _, row in filtered.iterrows():
    with st.container():
        st.markdown("---")
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
        with c1:
            st.markdown(f"**{row['patient_id']}**")
            st.caption(f"{row['age']} yo {row['sex']}, HbA1c: {row['hba1c']}")
            st.markdown(render_status_badge(row['data_status']), unsafe_allow_html=True)
        with c2:
            st.markdown(f"**Current:** {row['current_glucose']:.0f} mg/dL ({row['trend_direction']})" if pd.notna(row['current_glucose']) else "**Current:** N/A")
            st.markdown(render_band_badge(row['band']), unsafe_allow_html=True)
        with c3:
            fig = sparkline_figure(row['sparkline'])
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        with c4:
            st.write(f"TIR 24h: {row['tir_24h']:.0f}%" if pd.notna(row['tir_24h']) else "TIR 24h: N/A")
            st.write(f"Alerts 24h: {row['alerts_24h']}")
        with c5:
            if st.button("Open Twin", key=f"btn_{row['patient_id']}"):
                st.session_state["patient_id"] = row['patient_id']
                st.session_state["as_of"] = None # reset to default
                st.switch_page("pages/2_Live_Twin.py")
