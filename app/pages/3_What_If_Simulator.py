import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import streamlit as st

from app.components import (
    disclaimer_banner,
    render_band_badge,
    render_status_badge,
)
from src.app_lib.data_access import get_config
from src.app_lib.figures import (
    p_improvement_figure,
    whatif_effects_figure,
    whatif_fan_figure,
)
from src.app_lib.viewmodels import twin_view
from src.app_lib.whatif_vm import (
    available_scenarios,
    build_request,
    export_whatif_json,
    run_whatif_view,
    validation_summary,
)

st.set_page_config(layout="wide")
disclaimer_banner()
config = get_config()

st.markdown("""
<div style="background-color: #2c3e50; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <b>About the Simulator:</b> The twin estimates this patient's own glucose parameters from their recent history and simulates how plans would play out. These are model estimates, not predictions of what will certainly happen.
</div>
""", unsafe_allow_html=True)

if "patient_id" not in st.session_state or "as_of" not in st.session_state:
    st.warning("Please select a patient and a moment from the Live Twin page first.")
    st.stop()

pid = st.session_state["patient_id"]
current = st.session_state["as_of"]

# Context Bar
col_back, col_ctx = st.columns([1, 5])
with col_back:
    if st.button("← Back to Live Twin"):
        st.switch_page("pages/2_Live_Twin.py")

with col_ctx:
    view = twin_view(pid, current, include_actual_overlay=False)
    prof = view["profile"]
    kpis = view["kpis"]
    
    status_html = render_status_badge(view["data_quality"]["status"])
    band_html = render_band_badge(kpis['band']) if kpis['band'] else "N/A"
    g_val = f"{kpis['current_glucose']:.0f}" if kpis['current_glucose'] else "N/A"
    
    st.markdown(f"**Patient {pid}** | As of: {current.strftime('%Y-%m-%d %H:%M')} | Glucose: {g_val} | Risk: {band_html} | {status_html}", unsafe_allow_html=True)

is_stale_or_warming = view["data_quality"]["status"] in ["stale", "warming_up"]
if is_stale_or_warming:
    st.warning("Data Stale/Warming Up: Twin engine has suspended confident predictions. Proceed with caution.")

st.markdown("---")

col_plan, col_results = st.columns([1, 2])

with col_plan:
    st.subheader("Your plan")
    
    presets = config["app"].get("whatif_presets", [])
    preset_names = ["Custom"] + [p["name"] for p in presets]
    
    selected_preset_name = st.selectbox("Presets", preset_names)
    
    preset = None
    if selected_preset_name != "Custom":
        preset = next((p for p in presets if p["name"] == selected_preset_name), None)
        
    st.markdown("##### Meals")
    st.caption("Planned meals are treated as user-supplied scenario inputs, not predictions.")
    
    default_meal = preset["plan"].get("meal") if preset and "meal" in preset["plan"] else None
    
    plan_meal = st.checkbox("Plan a meal", value=default_meal is not None)
    
    meals = []
    if plan_meal:
        m_offset = st.slider("Minutes from now", 0, 120, default_meal["offset_min"] if default_meal else 20)
        m_carbs = st.slider("Carbs (g)", 10, 150, default_meal["carbs"] if default_meal else 60)
        meals.append({"offset_min": m_offset, "carbs_g": m_carbs})
        
        with st.expander("Add another meal"):
            plan_meal2 = st.checkbox("Plan second meal")
            if plan_meal2:
                m2_offset = st.slider("Minutes from now (Meal 2)", 0, 180, 120)
                m2_carbs = st.slider("Carbs (g) (Meal 2)", 10, 150, 40)
                meals.append({"offset_min": m2_offset, "carbs_g": m2_carbs})
                
    st.markdown("##### Scenarios to compare")
    scens = available_scenarios()
    
    selected_scenarios = []
    
    # Baseline is always selected
    selected_scenarios.append("baseline")
    
    for s in scens:
        if s["name"] == "baseline":
            continue
            
        disabled = s["needs_meal"] and not plan_meal
        default_sel = preset is not None and s["name"] in preset.get("scenarios", [])
        
        sel = st.checkbox(s["label"], value=default_sel and not disabled, disabled=disabled, help=s["description"])
        if disabled and s["needs_meal"]:
            st.caption("*(Requires a planned meal)*")
            
        if sel and not disabled:
            selected_scenarios.append(s["name"])
            
    custom_params = {}
    with st.expander("Customize a scenario"):
        add_custom_act = st.checkbox("Add custom activity")
        if add_custom_act:
            a_offset = st.slider("Start minutes from now", 0, 120, 15)
            a_dur = st.slider("Duration (min)", 5, 120, 30)
            a_int = st.selectbox("Intensity", [1, 2], format_func=lambda x: "Light" if x==1 else "Moderate")
            custom_params["custom_activity"] = {"offset_min": a_offset, "duration": a_dur, "intensity": a_int}
            selected_scenarios.append("custom")
            
    req, errors = build_request(meals, selected_scenarios, custom_params)
    
    if errors:
        for e in errors:
            st.error(e)
            
    run_disabled = errors or is_stale_or_warming
    
    if st.button("Run what-if", disabled=bool(run_disabled), type="primary"):
        if req:
            with st.spinner("Running simulator... (~1 second for cached posterior)"):
                try:
                    # serialize req
                    req_dict = {
                        "scenario_names": req.scenario_names,
                        "planned_meals": [{"time_offset_min": m.time_offset_min, "carbs_g": m.carbs_g} for m in req.planned_meals],
                        "baseline_activities": [{"start_offset_min": a.start_offset_min, "duration_min": a.duration_min, "intensity": a.intensity} for a in req.baseline_activities]
                    }
                    res = run_whatif_view(pid, current, req_dict)
                    st.session_state["whatif_result"] = res
                    st.session_state["whatif_req"] = req_dict
                except Exception as e:
                    st.error(f"Error: {e}")

with col_results:
    if st.button("Reset results"):
        if "whatif_result" in st.session_state:
            del st.session_state["whatif_result"]
            
    if "whatif_result" in st.session_state:
        res = st.session_state["whatif_result"]
        
        conf_color = "green" if res["metadata"]["confidence_level"] == "High" else "orange" if res["metadata"]["confidence_level"] == "Medium" else "red"
        
        if res["ranking"]:
            best = res["ranking"][0]
            best_s = next(s for s in res["scenarios"] if s["name"] == best)
            
            st.info(f"**Estimated best option: {best.replace('_', ' ').capitalize()}** - peak about {abs(best_s['delta_peak_median']):.0f} mg/dL lower, about {abs(best_s['delta_time_above_180_median']):.0f} fewer minutes above 180.")
            st.caption(f"Estimated ranking, not a recommendation. Confidence: :{conf_color}[{res['metadata']['confidence_level']}]")
        else:
            st.warning(f"No high/medium confidence safe options identified. Confidence: :{conf_color}[{res['metadata']['confidence_level']}]")
            
        fig_fan = whatif_fan_figure(res)
        st.plotly_chart(fig_fan, use_container_width=True)
        
        t1, t2, t3, t4 = st.tabs(["Effects", "Details per scenario", "How it works", "Consistency"])
        
        with t1:
            st.plotly_chart(whatif_effects_figure(res), use_container_width=True)
            st.plotly_chart(p_improvement_figure(res), use_container_width=True)
            
        with t2:
            for s in res["scenarios"]:
                with st.expander(f"{s['name'].replace('_', ' ').capitalize()}"):
                    st.write(s["summary_sentence"])
                    if s["hypo_risk"]:
                        st.error("Hypoglycemia risk detected.")
                        
        with t3:
            st.write(f"Computation time: {res['metadata']['compute_time_sec']:.2f} seconds")
            if res["metadata"]["confidence_reasons"]:
                st.write("**Confidence reasons:**")
                for r in res["metadata"]["confidence_reasons"]:
                    st.write(f"- {r}")
                    
        with t4:
            if res["metadata"]["forecast_agreement"]:
                st.write(res["metadata"]["forecast_agreement"])
            else:
                st.write("No consistency check available for this setup.")
                
        with st.expander("In-silico validation (synthetic ground truth, not available in real life)"):
            val = validation_summary()
            if val:
                st.json(val)
            else:
                st.write("Validation reports not found.")
            try:
                st.page_link("pages/4_Model_Insights.py", label="View full validation report")
            except Exception:
                try:
                    st.page_link("4_Model_Insights.py", label="View full validation report")
                except Exception:
                    pass
                
        st.download_button("Download what-if report (JSON)", data=export_whatif_json(res), file_name=f"whatif_{pid}.json")

st.markdown("---")
st.caption("Educational simulation with synthetic data. Estimates only. Not medical advice.")
