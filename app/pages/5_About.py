import streamlit as st
from app.components import disclaimer_banner

st.title("About DiaTwin")
disclaimer_banner()

st.write("""
DiaTwin is a Type 2 Diabetes Digital Twin engine prototype.
It uses synthetic data (EHR + wearable time-series) to generate a personalized twin state for each patient.

The patients shown in this application are DEMO PATIENTS ONLY, drawn from a frozen test split. 
No model tuning or training occurs within this app. The app only visualizes pre-computed and frozen logic.
""")
