import streamlit as st
import json
from pathlib import Path
from src.app_lib.data_access import AppStartupError, get_config, get_registry

st.set_page_config(page_title="DiaTwin", layout="wide")

try:
    config = get_config()
    registry = get_registry()
except AppStartupError as e:
    st.error(str(e))
    st.stop()

# Sidebar
st.sidebar.title(config["app"]["title"])
st.sidebar.caption(config["app"]["subtitle"])

if not config["app"].get("use_demo_bundle"):
    manifest = Path(config["evaluation"]["frozen_manifest_path"])
    if manifest.exists():
        with open(manifest, "r") as f:
            h = json.load(f)["hashes"]
            # show first 8 chars of a model hash
            v = list(h.values())[0][:8]
            st.sidebar.caption(f"Model version: {v}")

# Navigation
pgs = [
    st.Page("pages/1_Patient_List.py", title="Patient List", icon="👥"),
    st.Page("pages/2_Live_Twin.py", title="Live Twin", icon="❤️"),
    st.Page("pages/3_What_If_Simulator.py", title="What-if Simulator", icon="⚡"),
    st.Page("pages/4_Model_Insights.py", title="Model Insights", icon="🔍"),
    st.Page("pages/5_About.py", title="About", icon="ℹ️")
]
pg = st.navigation(pgs)
pg.run()
