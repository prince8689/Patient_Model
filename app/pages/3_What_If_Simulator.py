import streamlit as st
from app.components import disclaimer_banner

st.title("What-if Simulator")
disclaimer_banner()

st.info("Coming next (Day 12)")
st.write("Planned features:")
st.write("- Interactive scenario builder (Meals, Activity)")
st.write("- Counterfactual trajectory forecasting")
st.write("- Oracle evaluation comparison")
