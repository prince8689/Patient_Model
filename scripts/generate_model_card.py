import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config


def main():
    config = load_config()
    reports_path = Path(config["paths"]["reports"])
    models_path = Path(config["paths"]["models"])
    
    with open(reports_path / "metrics_test_day7.json", "r") as f:
        metrics = json.load(f)
        
    with open(models_path / "thresholds_v1.json", "r") as f:
        thresholds = json.load(f)["thresholds"]
        
    with open(models_path / "FROZEN.json", "r") as f:
        frozen = json.load(f)
        
    xgb_m = metrics["xgb_metrics"]
    prev = metrics["prevalence"]
    med_cm = metrics["threshold_metrics"]["medium"]["confusion_matrix"]
    
    t_med = thresholds["t_medium"]
    t_high = thresholds["t_high"]
    
    # Just format the markdown
    card = f"""# DiaTwin Model Card (v1.0)

## Model Details
- **Type**: XGBoost Classifier
- **Version**: v1.0
- **Features**: 75 engineered time-series and static features covering Glucose, Meals, Activity, Heart Rate, Sleep, Time, EHR, Personal Baseline, and Missingness.
- **Training Data**: Synthetic tabular dataset (simulating EHR + Wearable signals) representing ~28 patients in the training set.

## Intended Use
- **Primary Use**: Predicting glucose spikes (increase of >= 50 mg/dL) up to 2 hours in advance in Type 2 Diabetes patients.
- **Target Audience**: Healthcare providers testing interventions in a simulated "what-if" environment.

## Out-of-Scope Use
- Not for clinical deployment or real-world diagnostics.
- Not for Type 1 Diabetes management or automated insulin delivery.

## Data
- **Source**: 100% synthetically generated.
- **Splits**: Strict patient-wise stratification (Train 70% / Val 15% / Test 15%).

## Metrics (Test Set)
- **Prevalence**: {prev:.2%}
- **ROC-AUC**: {xgb_m["roc_auc"]["mean"]:.3f} (95% CI: {xgb_m["roc_auc"]["ci_lower"]:.3f}-{xgb_m["roc_auc"]["ci_upper"]:.3f})
- **PR-AUC**: {xgb_m["pr_auc"]["mean"]:.3f} (95% CI: {xgb_m["pr_auc"]["ci_lower"]:.3f}-{xgb_m["pr_auc"]["ci_upper"]:.3f})
- **Brier Score**: {xgb_m["brier"]["mean"]:.4f}
- **Log Loss**: {xgb_m["log_loss"]["mean"]:.4f}
- **ECE**: {xgb_m["ece"]["mean"]:.4f}

## Calibration
- **Method**: Isotonic Regression fitted on Out-of-Fold training predictions.
- **Result**: Probabilities map closely to empirical event rates.

## Thresholds and Risk Bands
- **Low Risk**: < {t_med:.4f}
- **Medium Risk**: [{t_med:.4f}, {t_high:.4f})
- **High Risk**: >= {t_high:.4f}

## Explainability
- **Method**: SHAP (TreeExplainer)
- **Top Drivers**: 
  1. glu_current
  2. meal_carbs_last_60m
  3. glu_delta_30m
  4. meal_min_since_last

## Clinical-Utility Results
- **Alert Burden (Medium)**: TBD
- **Event-Level Recall**: TBD
- **Median Lead Time**: TBD

## Subgroup Performance
(Generated via scripts/error_analysis.py)

## Limitations
- Built entirely on synthetic data.
- Tested on very small sample sizes.
- No real-world validation; no regulatory clearance.

## Reproducibility
- Seed: 42
- Commit Hash: {frozen["git_commit"]}
"""

    with open(Path("docs") / "MODEL_CARD.md", "w") as f:
        f.write(card)
        
    print("MODEL_CARD.md generated.")

if __name__ == "__main__":
    main()
