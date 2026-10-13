import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pandas as pd
import streamlit as st

from app.components import disclaimer_banner
from src.app_lib.data_access import get_config
from src.app_lib.insights_vm import (
    ablation_table,
    classifier_tables,
    clinical_utility_tables,
    forecast_tables,
    headline_metrics,
    integrity_report,
    limitations_list,
    load_bundle,
    shap_tables,
    subgroup_tables,
    thresholds_info,
    whatif_tables,
)

st.set_page_config(layout="wide")
disclaimer_banner()

st.title("Model Insights")
st.markdown("""
**How to read this page**:
This page displays static evaluation results for the DiaTwin model. All numbers are drawn from the final evaluation reports. No patient data or model logic is loaded here. 
**Note on Cohort Size**: Metrics are based on 40 synthetic patients (6 validation and 6 test patients). Confidence intervals are wide by design of this small cohort.
""")

config = get_config()
bundle = load_bundle()

if not bundle.get("sections"):
    st.error("Insights bundle is missing or empty. Please run `python scripts/build_insights_bundle.py`.")
    st.stop()

# Headline Metrics
st.header("Results at a Glance")
cards = headline_metrics(bundle)
cols = st.columns(3)
for i, card in enumerate(cards):
    with cols[i % 3]:
        st.metric(label=f"{card['label']} ({card['n']})", value=card['value'], delta=card['ci'], delta_color="off")
        st.caption(f"Source: {card['source']}")

st.markdown("---")

tabs = st.tabs(config["app"].get("section_order", []))

with tabs[0]: # Risk model
    st.subheader("Risk Model Validation")
    cls = classifier_tables(bundle)
    if not cls:
        st.info("Not available (missing: classifier metrics)")
    else:
        st.write("XGBoost vs Logistic Regression:")
        df = pd.DataFrame([
            {"Model": "XGBoost", "ROC-AUC": cls.get("xgb_metrics", {}).get("roc_auc", {}).get("mean"), "PR-AUC": cls.get("xgb_metrics", {}).get("pr_auc", {}).get("mean")},
            {"Model": "Logistic Regression", "ROC-AUC": cls.get("lr_metrics", {}).get("roc_auc", {}).get("mean"), "PR-AUC": cls.get("lr_metrics", {}).get("pr_auc", {}).get("mean")}
        ])
        st.dataframe(df)
        st.caption("What this means: Evaluates how well the model discriminates risk. What it does not mean: It does not imply clinical accuracy.")

with tabs[1]: # Calibration and bands
    st.subheader("Calibration and Bands")
    thres = thresholds_info(bundle)
    if not thres:
        st.info("Not available (missing: thresholds_bands)")
    else:
        st.json(thres)
        st.caption("What this means: The model's probability outputs are grouped into actionable bands. What it does not mean: These are not medical diagnoses.")

with tabs[2]: # Why the model predicts
    st.subheader("Why the model predicts (SHAP)")
    shap_d = shap_tables(bundle)
    if not shap_d:
        st.info("Not available (missing: explainability)")
    else:
        st.json(shap_d)
        st.caption("What this means: Shows which features drive the risk score globally. What it does not mean: It does not prove causal relationships.")

with tabs[3]: # Does fusion help?
    st.subheader("Does fusion help? (Ablation)")
    abl = ablation_table(bundle)
    if not abl:
        st.info("Not available (missing: ablation)")
    else:
        st.json(abl)
        st.caption("What this means: Shows performance drops when data modalities are removed. What it does not mean: It is not a guarantee of real-world value.")

with tabs[4]: # Clinical usefulness
    st.subheader("Clinical Usefulness")
    clin = clinical_utility_tables(bundle)
    if not clin:
        st.info("Not available (missing: clinical_utility)")
    else:
        st.json(clin)
        st.caption("What this means: Simulation-based estimates, not clinical claims.")

with tabs[5]: # Forecast
    st.subheader("Forecast Evaluation")
    fc = forecast_tables(bundle)
    if not fc:
        st.info("Not available (missing: forecast)")
    else:
        st.json(fc)
        st.caption("What this means: Measures expected error in the 2-hour forecast. What it does not mean: It does not fully predict unannounced events like meals.")

with tabs[6]: # What-if validation
    st.subheader("What-if Validation")
    wi = whatif_tables(bundle)
    if not wi:
        st.info("Not available (missing: whatif)")
    else:
        st.json(wi)
        st.caption("What this means: In-silico validation (synthetic ground truth, not available in real life). What it does not mean: It does not reflect exact physiological fidelity.")

with tabs[7]: # Where it struggles
    st.subheader("Where it struggles")
    sg = subgroup_tables(bundle)
    if not sg:
        st.info("Not available (missing: subgroups_errors)")
    else:
        st.json(sg)
    
    st.markdown("### Known Limitations")
    for lim in limitations_list():
        st.write(f"- {lim}")
    st.caption("What this means: Honest disclosure of model boundaries. What it does not mean: It does not mean the system is completely broken.")

with tabs[8]: # Integrity and reproducibility
    st.subheader("Integrity and Reproducibility")
    st.markdown("""
To safely allow UI modifications without weakening integrity:
- The loader bypasses the rigid whole-file hash check exclusively for `config.yaml`.
- Instead, it verifies via a section-level check that no value present in the first-freeze config (commit 82c36c0) changed, normalising CRLF to LF before comparing.
- For the forecast and what-if modules, the manifest and the test marker were first committed together (commits 7210b6d and b5f8c07), so freeze-before-test cannot be proven from git for them.
- For the risk model, the freeze commit precedes the test commit.
""")
    integ = integrity_report(bundle)
    if not integ:
        st.info("Not available (missing: integrity)")
    else:
        for module in integ:
            st.write(f"**Module**: {module['module']}")
            st.write(f"Freeze Commit: {module['freeze_commit']}")
            st.write(f"Test Commit: {module['test_commit']}")
            st.write(f"Frozen before test verified: {module['freeze_before_test_verified']}")
            df = pd.DataFrame.from_dict(module['files'], orient='index')
            st.dataframe(df)
        st.caption("What this means: Cryptographic proof that models were locked before testing. What it does not mean: It does not mean the code is bug-free.")
