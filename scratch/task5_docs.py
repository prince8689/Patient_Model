
import json

with open('reports/realism_comparison.json', 'r') as f:
    data = json.load(f)

md = f'''# Realism Comparison

This document compares the synthetic cohort against the real data (Shanghai T2DM dataset).

## Counts
| Metric | Real | Synthetic |
|---|---|---|
| Patients | {data['real_counts']['patients']} | {data['synthetic_counts']['patients']} |
| Recordings | {data['real_counts']['recordings']} | {data['synthetic_counts']['recordings']} |
| Samples | {data['real_counts']['samples']} | {data['synthetic_counts']['samples']} |

## Metrics Table

| Metric | Real | Synthetic | Distance |
|---|---|---|---|
| Use Insulin | {data['real_use_insulin']:.4f} | {data['synthetic_use_insulin']:.4f} | {abs(data['real_use_insulin'] - data['synthetic_use_insulin']):.4f} |
| Label Prevalence | {data['real_label_prevalence']:.4f} | {data['synthetic_label_prevalence']:.4f} | {abs(data['real_label_prevalence'] - data['synthetic_label_prevalence']):.4f} |
| Gap Count (15m grid) | {data['real_gaps']['count']} | {data['synthetic_gaps']['15m_grid']['count']} | {abs(data['real_gaps']['count'] - data['synthetic_gaps']['15m_grid']['count'])} |
| Gap Median (15m grid, min) | {data['real_gaps']['median_min']:.1f} | {data['synthetic_gaps']['15m_grid']['median_min']:.1f} | {abs(data['real_gaps']['median_min'] - data['synthetic_gaps']['15m_grid']['median_min']):.1f} |
| Meal Rise (mg/dL) | {data['real_meal_rise_mean']} | {data['synthetic_meal_rise_mean']:.2f} | N/A |
| Regression Slope (HbA1c to mean glucose) | {data['real_regression']['slope']:.2f} | {data['synthetic_regression']['slope']:.2f} | {abs(data['real_regression']['slope'] - data['synthetic_regression']['slope']):.2f} |
| Regression Intercept | {data['real_regression']['intercept']:.2f} | {data['synthetic_regression']['intercept']:.2f} | {abs(data['real_regression']['intercept'] - data['synthetic_regression']['intercept']):.2f} |
| Regression R-squared | {data['real_regression']['r_squared']:.4f} | {data['synthetic_regression']['r_squared']:.4f} | {abs(data['real_regression']['r_squared'] - data['synthetic_regression']['r_squared']):.4f} |

## Metric-by-Metric Reading

*   **Insulin Use:** The synthetic cohort has lower insulin usage compared to the real dataset.
*   **Label Prevalence:** The prevalence of spikes is extremely close.
*   **Gaps:** The synthetic data has many more frequent but shorter gaps on the 15-minute grid compared to the real data which has fewer but longer gaps.
*   **Meal Rise:** Meal rise is not computable on the real data, but the synthetic data shows a mean meal rise of 61.06 mg/dL.
*   **HbA1c Regression:** The real data has a much weaker correlation (R-squared 0.25) between HbA1c and mean glucose compared to the synthetic data (R-squared 0.71). The slope is also significantly steeper in the synthetic data.

## Required Changes for a New Synthetic Cohort

To improve realism, a new synthetic cohort needs:
1.  A higher proportion of patients on insulin to match the real prevalence of 32%.
2.  A more realistic gap generation mechanism that creates fewer but longer sensor outages rather than many short missing readings.
3.  A more realistic mapping from HbA1c to mean glucose, specifically lowering the correlation and flattening the slope to better reflect the variance seen in real populations.
'''
with open('docs/REALISM.md', 'w') as f:
    f.write(md)

