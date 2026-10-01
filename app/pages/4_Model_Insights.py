import streamlit as st
from app.components import disclaimer_banner

st.title("Model Insights")
disclaimer_banner()

st.info("Coming next (Day 13)")
st.write("Planned features:")
st.write("- Global SHAP feature importance")
st.write("- Threshold calibration curves")
st.write("- Test split metrics summary")
