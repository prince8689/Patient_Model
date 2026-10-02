import streamlit as st

from src.app_lib.data_access import get_config


def disclaimer_banner():
    config = get_config()
    text = config["app"]["disclaimer"]
    st.info(f"**DISCLAIMER**: {text}")

def render_band_badge(band: str) -> str:
    config = get_config()
    palette = config["app"]["palette"]
    color = palette.get(band.lower(), "#95a5a6")
    return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-weight: bold; font-size: 0.8em;">{band}</span>'

def kpi_card(title: str, value: str, subvalue: str = None):
    st.markdown(f"**{title}**<br><span style='font-size: 1.5em; font-weight: bold;'>{value}</span>", unsafe_allow_html=True)
    if subvalue:
        st.caption(subvalue)
        
def render_status_badge(status: str) -> str:
    if status == "ok":
        return '<span style="background-color: #2ecc71; color: white; padding: 2px 8px; border-radius: 12px; font-weight: bold; font-size: 0.8em;">Data OK</span>'
    elif status == "warming_up":
        return '<span style="background-color: #f39c12; color: white; padding: 2px 8px; border-radius: 12px; font-weight: bold; font-size: 0.8em;">Warming Up</span>'
    elif status == "stale":
        return '<span style="background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 12px; font-weight: bold; font-size: 0.8em;">Stale Data</span>'
    elif status == "no_glucose":
        return '<span style="background-color: #f1c40f; color: black; padding: 2px 8px; border-radius: 12px; font-weight: bold; font-size: 0.8em;">No Current Glucose</span>'
    else:
        return f'<span style="background-color: #95a5a6; color: white; padding: 2px 8px; border-radius: 12px; font-weight: bold; font-size: 0.8em;">{status}</span>'
