import json
from pathlib import Path

from src.app_lib.data_access import get_config


def load_bundle():
    config = get_config()
    path = Path(config["app"].get("insights_bundle_path", "reports/insights_bundle.json"))
    if not path.exists():
        return {"sections": {}, "missing": {"bundle": f"File {path} not found"}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def headline_metrics(bundle):
    # 6 headline cards
    cls = bundle.get("sections", {}).get("classifier", {}).get("data", {})
    whatif = bundle.get("sections", {}).get("whatif", {}).get("data", {})
    integ = bundle.get("sections", {}).get("integrity", {}).get("data", [])
    
    # 1. ROC-AUC
    if cls and "xgb_metrics" in cls and "roc_auc" in cls["xgb_metrics"]:
        val = cls["xgb_metrics"]["roc_auc"]
        card1 = {"label": "Classifier ROC-AUC (Test)", "value": f"{val['mean']:.3f}", "ci": f"[{val['ci_lower']:.3f}, {val['ci_upper']:.3f}]", "n": "N=6 test patients", "source": "metrics_test_day7.json"}
    else:
        card1 = {"label": "Classifier ROC-AUC", "value": "N/A", "ci": "N/A", "n": "", "source": ""}

    # 2. PR-AUC
    if cls and "xgb_metrics" in cls and "pr_auc" in cls["xgb_metrics"]:
        val = cls["xgb_metrics"]["pr_auc"]
        card2 = {"label": "Classifier PR-AUC (Test)", "value": f"{val['mean']:.3f}", "ci": f"[{val['ci_lower']:.3f}, {val['ci_upper']:.3f}]", "n": "N=6 test patients", "source": "metrics_test_day7.json"}
    else:
        card2 = {"label": "Classifier PR-AUC", "value": "N/A", "ci": "N/A", "n": "", "source": ""}
        
    # 3. Forecast MAE
    fc = bundle.get("sections", {}).get("forecast", {}).get("data", {})
    if fc and "mae_60m" in fc:
        card3 = {"label": "Forecast MAE @ 60m (Test)", "value": f"{fc['mae_60m']:.1f} mg/dL", "ci": "no interval available", "n": "N=6 test patients", "source": "forecast_metrics"}
    else:
        card3 = {"label": "Forecast MAE @ 60m", "value": "N/A", "ci": "N/A", "n": "", "source": ""}
        
    # 4. Forecast Coverage
    if fc and "coverage_80" in fc:
        card4 = {"label": "Forecast 80% Coverage", "value": f"{fc['coverage_80']*100:.1f}%", "ci": "no interval available", "n": "N=6 test patients", "source": "forecast_metrics"}
    else:
        card4 = {"label": "Forecast 80% Coverage", "value": "N/A", "ci": "N/A", "n": "", "source": ""}
        
    # 5. Alert Burden
    clin = bundle.get("sections", {}).get("clinical_utility", {}).get("data", {})
    if clin and "alerts_per_day" in clin:
        card5 = {"label": "Alerts per patient-day", "value": f"{clin['alerts_per_day']:.1f}", "ci": "no interval available", "n": "N=6 test patients", "source": "clinical_utility"}
    else:
        card5 = {"label": "Alerts per patient-day", "value": "N/A", "ci": "N/A", "n": "", "source": ""}
        
    # 6. Integrity
    fbt = all([r.get("freeze_before_test_verified", False) for r in integ]) if integ else False
    if fbt:
        card6 = {"label": "Protocol", "value": "Frozen before test: verified", "ci": "", "n": "Git log", "source": "Manifests"}
    else:
        card6 = {"label": "Protocol", "value": "Frozen before test: not verified", "ci": "", "n": "Git log", "source": "Manifests"}
        
    return [card1, card2, card3, card4, card5, card6]

def classifier_tables(bundle):
    cls = bundle.get("sections", {}).get("classifier", {}).get("data", {})
    return cls

def calibration_curves(bundle):
    return bundle.get("sections", {}).get("calibration", {}).get("data")
    
def thresholds_info(bundle):
    return bundle.get("sections", {}).get("thresholds_bands", {}).get("data")
    
def shap_tables(bundle):
    return bundle.get("sections", {}).get("explainability", {}).get("data")
    
def ablation_table(bundle):
    return bundle.get("sections", {}).get("ablation", {}).get("data")
    
def clinical_utility_tables(bundle):
    return bundle.get("sections", {}).get("clinical_utility", {}).get("data")
    
def forecast_tables(bundle):
    return bundle.get("sections", {}).get("forecast", {}).get("data")
    
def whatif_tables(bundle):
    return bundle.get("sections", {}).get("whatif", {}).get("data")
    
def subgroup_tables(bundle):
    return bundle.get("sections", {}).get("subgroups_errors", {}).get("data")
    
def integrity_report(bundle):
    return bundle.get("sections", {}).get("integrity", {}).get("data", [])

def glossary():
    config = get_config()
    return config["app"].get("glossary", [])
    
def guided_demo_steps():
    config = get_config()
    return config["app"].get("guided_demo_steps", [])
    
def challenge_mapping():
    return [
        {"Requirement": "Proof-of-concept digital twin", "Implementation": "DiaTwin Engine (src/twin/engine.py)", "Notes": "Fully functional digital twin state reconstruction"},
        {"Requirement": "Dynamic virtual replica", "Implementation": "Live Twin Page", "Notes": "Reconstructs state dynamically"},
        {"Requirement": "Integrate real-time wearable data with EHR", "Implementation": "Feature engineering pipeline", "Notes": "Fuses static profile with time-series"},
        {"Requirement": "Predict adverse health events", "Implementation": "Risk module (XGBoost)", "Notes": "Predicts spikes in next 2 hours"},
        {"Requirement": "Personalize treatment protocols", "Implementation": "What-if Simulator", "Notes": "Treatment personalization is limited to lifestyle scenarios: meals and activity; no medication changes"},
        {"Requirement": "GitHub repository with documentation", "Implementation": "docs/ folder", "Notes": "Docs included"},
        {"Requirement": "Working prototype demo", "Implementation": "Streamlit App", "Notes": "Demo bundle mode enabled"}
    ]

def limitations_list():
    return [
        "Synthetic data and simplified physiology",
        "The model is for Type 2 diabetes and predicts a glucose rise of 50 mg/dL or more within 2 hours",
        "40 synthetic patients, 6 test patients so wide confidence intervals",
        "Simulator and twin share a model family in what-if evaluation",
        "No real-world validation; no regulatory clearance",
        "Unannounced meals and events",
        "No insulin or medication modelling",
        "For the What-if Simulator test evaluation (6 test patients), the peak error is 1.0, 10.2 and 11.5 mg/dL for the three tested scenarios (reports/WHATIF_TEST_DONE.json). The 80% interval coverage is 0%, 17% and 0%. The uncertainty bands significantly under-cover.",
        "Forecast test metrics were not saved and a new held-out evaluation is planned.",
        "The synthetic data differ from the real cohort in glucose level: mean glucose is 219.30 mg/dL in synthetic vs 141.01 mg/dL in real cohort; time above 180 is 68.6% vs 19.6% (from reports/realism_comparison.json).",
        "Integrity record: the risk model freeze precedes its test evaluation in git history; for the forecast and what-if modules the manifest and the test marker were committed together so freeze-before-test cannot be shown from git."
    ]
