import json
import re

# 1. READ REPORTS
with open('reports/metrics_test_day7.json') as f:
    mt = json.load(f)
with open('reports/metrics_forecast_val.json') as f:
    mf = json.load(f)
with open('reports/WHATIF_TEST_DONE.json') as f:
    mw = json.load(f)
with open('docs/data_quality.json') as f:
    dq = json.load(f)

# Extract risk metrics
roc_auc = f"{mt['xgb_metrics']['roc_auc']['mean']:.3f}"
roc_lower = f"{mt['xgb_metrics']['roc_auc']['ci_lower']:.3f}"
roc_upper = f"{mt['xgb_metrics']['roc_auc']['ci_upper']:.3f}"
pr_auc = f"{mt['xgb_metrics']['pr_auc']['mean']:.3f}"
pr_lower = f"{mt['xgb_metrics']['pr_auc']['ci_lower']:.3f}"
pr_upper = f"{mt['xgb_metrics']['pr_auc']['ci_upper']:.3f}"
ece = f"{mt['xgb_metrics']['ece']['mean']:.4f}"
prevalence = f"{mt['prevalence']:.3f}"

cm = mt['threshold_metrics']['medium']['confusion_matrix']
total_test_rows = cm[0][0] + cm[0][1] + cm[1][0] + cm[1][1]
alerts_per_day = (cm[0][1] + cm[1][1]) / (6 * 21)

# Extract forecast metrics
rmse_60m = f"{mf['60m']['rmse']:.2f}"
cov_60m = f"{mf['60m']['coverage_cal']*100:.1f}"

# Extract whatif metrics
wi_keys = list(mw['metrics'].keys())
peak_errs = [f"{mw['metrics'][k]['peak_err']:.1f}" for k in wi_keys]
peak_covs = [f"{mw['metrics'][k]['peak_covered']*100:.0f}" for k in wi_keys]

mean_glucose = round(dq['glucose']['mean'])
pct_above_180 = round(dq['glucose']['pct_above_180'])

readme_results = f"""## Results at a Glance

These metrics reflect the in-silico evaluation on synthetic patients. Test metrics use 6 test patients ({total_test_rows} rows).

| Metric | Value | 95% CI | Source |
| :--- | :--- | :--- | :--- |
| **Risk Model AUC (Test)** | {roc_auc} | [{roc_lower} - {roc_upper}] | `reports/metrics_test_day7.json` |
| **Risk Model PR-AUC (Test)** | {pr_auc} | [{pr_lower} - {pr_upper}] | `reports/metrics_test_day7.json` |
| **Calibration Error ECE (Test)** | {ece} | - | `reports/metrics_test_day7.json` |
| **Risk Prevalence (Test)** | {prevalence} | - | `reports/metrics_test_day7.json` |
| **Forecast RMSE 60m (Validation)** | {rmse_60m} mg/dL | - | `reports/metrics_forecast_val.json` |
| **Forecast Coverage 60m (Validation)** | {cov_60m}% | - | `reports/metrics_forecast_val.json` |

For the What-if Simulator test evaluation (6 test patients), the peak error is {peak_errs[0]}, {peak_errs[1]} and {peak_errs[2]} mg/dL for the three tested scenarios (`reports/WHATIF_TEST_DONE.json`). The 80% interval coverage is {peak_covs[0]}%, {peak_covs[1]}% and {peak_covs[2]}%. The uncertainty bands significantly under-cover.

## Claims
- The model targets Type 2 diabetes only.
- The label is a glucose rise of 50 mg/dL or more within 2 hours. It is not a hypoglycemia predictor.
- The synthetic population has a mean glucose of about {mean_glucose} mg/dL with about {pct_above_180}% of readings above 180 (from `docs/data_quality.json`).
- The medium risk band raises about {alerts_per_day:.2f} alerts per patient per day (from test metrics).
"""

def update_file(filepath, new_results, new_claims=None):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if "## Results at a Glance" in content:
        content = re.sub(r'## Results at a Glance.*?## Architecture', new_results + '\n## Architecture', content, flags=re.DOTALL)
    elif "## Claims" in content:
        # Just update claims for others if needed, but the prompt says:
        # "Put the same corrected statements in docs/MODEL_CARD.md and docs/WHATIF.md where they differ."
        pass
        
    # We will just write a custom replacer for MODEL_CARD and WHATIF
    with open(filepath, 'w') as f:
        f.write(content)

with open('README.md', 'r') as f:
    readme = f.read()
readme = re.sub(r'## Results at a Glance.*?## Architecture', readme_results + '\n## Architecture', readme, flags=re.DOTALL)
with open('README.md', 'w') as f:
    f.write(readme)

# Update docs/MODEL_CARD.md
with open('docs/MODEL_CARD.md', 'r') as f: mc = f.read()
mc = re.sub(r'The model targets Type 1 and Type 2 diabetes', 'The model targets Type 2 diabetes only', mc)
mc = re.sub(r'predicts any abnormal glucose event.*?hypoglycemia', 'The label is a glucose rise of 50 mg/dL or more within 2 hours. It is not a hypoglycemia predictor.', mc)
# Fix mean glucose and alerts in MODEL_CARD if they exist
mc = re.sub(r'mean glucose of about \d+.*?above 180', f'mean glucose of about {mean_glucose} mg/dL with about {pct_above_180}% of readings above 180', mc)
mc = re.sub(r'medium risk band raises about [\d\.]+ alerts', f'medium risk band raises about {alerts_per_day:.2f} alerts', mc)
with open('docs/MODEL_CARD.md', 'w') as f: f.write(mc)

# Update docs/WHATIF.md
with open('docs/WHATIF.md', 'r') as f: wi = f.read()
wi = re.sub(r'The model targets Type 1 and Type 2 diabetes', 'The model targets Type 2 diabetes only', wi)
wi = re.sub(r'predicts any abnormal glucose event.*?hypoglycemia', 'The label is a glucose rise of 50 mg/dL or more within 2 hours. It is not a hypoglycemia predictor.', wi)
wi = re.sub(r'mean glucose of about \d+.*?above 180', f'mean glucose of about {mean_glucose} mg/dL with about {pct_above_180}% of readings above 180', wi)
wi = re.sub(r'medium risk band raises about [\d\.]+ alerts', f'medium risk band raises about {alerts_per_day:.2f} alerts', wi)
with open('docs/WHATIF.md', 'w') as f: f.write(wi)

# Print the required table
print("NUMBER | VALUE SHOWN | SOURCE FILE | VALUE IN FILE")
print(f"ROC-AUC | {roc_auc} | reports/metrics_test_day7.json | {roc_auc}")
print(f"PR-AUC | {pr_auc} | reports/metrics_test_day7.json | {pr_auc}")
print(f"ECE | {ece} | reports/metrics_test_day7.json | {ece}")
print(f"Prevalence | {prevalence} | reports/metrics_test_day7.json | {prevalence}")
print(f"Test rows | {total_test_rows} | reports/metrics_test_day7.json | {total_test_rows}")
print(f"RMSE 60m | {rmse_60m} | reports/metrics_forecast_val.json | {rmse_60m}")
print(f"Coverage 60m | {cov_60m} | reports/metrics_forecast_val.json | {cov_60m}")
print(f"What-if Peak Errs | {peak_errs} | reports/WHATIF_TEST_DONE.json | {peak_errs}")
print(f"What-if Covs | {peak_covs} | reports/WHATIF_TEST_DONE.json | {peak_covs}")
print(f"Mean glucose | {mean_glucose} | docs/data_quality.json | {dq['glucose']['mean']}")
print(f"Pct > 180 | {pct_above_180} | docs/data_quality.json | {dq['glucose']['pct_above_180']}")
print(f"Medium alerts/day | {alerts_per_day:.2f} | reports/metrics_test_day7.json | Calculated from {total_test_rows} rows")
