import json
import pandas as pd

def build_md():
    with open('reports/realism_comparison.json') as f:
        data = json.load(f)

    # 1. Gather all differences for ordering by magnitude of gap
    changes = []
    
    # helper for pct
    def pct_diff(r, s):
        if r == 0: return float('inf')
        return abs(r - s) / abs(r)
    
    real_mean_glu = data['mean_glucose']['real']
    synth_mean_glu = data['mean_glucose']['synthetic']
    changes.append({
        'name': 'Mean Glucose (mg/dL) and Time Above 180',
        'desc': f"The synthetic mean glucose ({synth_mean_glu:.2f}) is significantly higher than real ({real_mean_glu:.2f}). Time above 180 must drop from {data['time_above_180']['synthetic']:.4f} to {data['time_above_180']['real']:.4f}.",
        'gap': pct_diff(real_mean_glu, synth_mean_glu)
    })
    
    changes.append({
        'name': 'Gap Statistics (15m grid)',
        'desc': f"Synthetic gaps per 1000 slots ({data['gap_stats_15m']['synthetic']['gaps_per_1000_slots']:.2f}) are much higher than real ({data['gap_stats_15m']['real']['gaps_per_1000_slots']:.2f}). The generator should produce fewer gaps, but with longer median length ({data['gap_stats_15m']['synthetic']['median']:.1f} vs {data['gap_stats_15m']['real']['median']:.1f} mins).",
        'gap': pct_diff(data['gap_stats_15m']['real']['gaps_per_1000_slots'], data['gap_stats_15m']['synthetic']['gaps_per_1000_slots'])
    })
    
    real_slope = data['regression_hba1c_glucose']['real']['slope']
    synth_slope = data['regression_hba1c_glucose']['synthetic']['slope']
    changes.append({
        'name': 'HbA1c to Mean Glucose Slope',
        'desc': f"The synthetic slope ({synth_slope:.2f}) is much steeper than the real cohort ({real_slope:.2f}). The generator should flatten this relationship.",
        'gap': pct_diff(real_slope, synth_slope)
    })
    
    real_cv = data['cv_glucose']['real']
    synth_cv = data['cv_glucose']['synthetic']
    changes.append({
        'name': 'Coefficient of Variation (CV)',
        'desc': f"The synthetic CV ({synth_cv:.4f}) is lower than the real CV ({real_cv:.4f}), meaning the synthetic glucose is less variable relative to its mean.",
        'gap': pct_diff(real_cv, synth_cv)
    })
    
    real_tbr = data['time_below_70']['real']
    synth_tbr = data['time_below_70']['synthetic']
    changes.append({
        'name': 'Time Below 70',
        'desc': f"The synthetic time below 70 ({synth_tbr:.4f}) is lower than the real cohort ({real_tbr:.4f}).",
        'gap': pct_diff(real_tbr, synth_tbr)
    })
    
    real_bmi = data['bmi']['real']
    synth_bmi = data['bmi']['synthetic']
    changes.append({
        'name': 'BMI',
        'desc': f"Synthetic BMI ({synth_bmi:.1f}) is higher than real ({real_bmi:.1f}).",
        'gap': pct_diff(real_bmi, synth_bmi)
    })
    
    real_age = data['age']['real']
    synth_age = data['age']['synthetic']
    changes.append({
        'name': 'Age',
        'desc': f"Synthetic Age ({synth_age:.1f}) is lower than real ({real_age:.1f}).",
        'gap': pct_diff(real_age, synth_age)
    })
    
    real_ins = data['insulin_use']['real']
    synth_ins = data['insulin_use']['synthetic']
    changes.append({
        'name': 'Insulin Use',
        'desc': f"Synthetic insulin use ({synth_ins:.4f}) is lower than real ({real_ins:.4f}).",
        'gap': pct_diff(real_ins, synth_ins)
    })
    
    # Sort changes by relative gap magnitude descending
    changes.sort(key=lambda x: x['gap'], reverse=True)
    
    # Format hour profile
    real_hour = pd.Series(data['hour_profile']['real'])
    synth_hour = pd.Series(data['hour_profile']['synthetic'])
    real_peak_idx = real_hour.astype(float).idxmax()
    real_peak_val = real_hour.astype(float).max()
    real_trough_idx = real_hour.astype(float).idxmin()
    real_trough_val = real_hour.astype(float).min()
    
    synth_peak_idx = synth_hour.astype(float).idxmax()
    synth_peak_val = synth_hour.astype(float).max()
    synth_trough_idx = synth_hour.astype(float).idxmin()
    synth_trough_val = synth_hour.astype(float).min()
    
    profile_desc = (
        f"The synthetic profile peaks at {synth_peak_idx}:00 ({synth_peak_val:.2f}) and is lowest at {synth_trough_idx}:00 ({synth_trough_val:.2f}). "
        f"The real profile peaks at {real_peak_idx}:00 ({real_peak_val:.2f}) and is lowest at {real_trough_idx}:00 ({real_trough_val:.2f})."
    )
    
    # Insert profile into changes manually with a high priority or as a separate point
    changes.insert(2, {
        'name': 'Hour-of-Day Profile',
        'desc': profile_desc
    })
    
    # Write the markdown
    md = f"""# Realism Comparison

This document compares the synthetic cohort against the real data (Shanghai T2DM dataset).

## Metrics Table
| Metric | Real | Synthetic |
|---|---|---|
| Patients | {data['patients']['real']} | {data['patients']['synthetic']} |
| Recordings | {data['recordings']['real']} | {data['recordings']['synthetic']} |
| Observed Samples | {data['observed_samples']['real']} | {data['observed_samples']['synthetic']} |
| Total Slots | {data['total_slots']['real']} | {data['total_slots']['synthetic']} |
| Mean Glucose (mg/dL) | {data['mean_glucose']['real']:.2f} | {data['mean_glucose']['synthetic']:.2f} |
| Std Glucose (mg/dL) | {data['std_glucose']['real']:.2f} | {data['std_glucose']['synthetic']:.2f} |
| CV Glucose | {data['cv_glucose']['real']:.4f} | {data['cv_glucose']['synthetic']:.4f} |
| Time Below 70 (%) | {data['time_below_70']['real']:.4f} | {data['time_below_70']['synthetic']:.4f} |
| Time 70-180 (%) | {data['time_70_180']['real']:.4f} | {data['time_70_180']['synthetic']:.4f} |
| Time Above 180 (%) | {data['time_above_180']['real']:.4f} | {data['time_above_180']['synthetic']:.4f} |
| Label Prevalence | {data['label_prevalence']['real']:.4f} | {data['label_prevalence']['synthetic']:.4f} |
| Age | {data['age']['real']:.1f} | {data['age']['synthetic']:.1f} |
| BMI | {data['bmi']['real']:.1f} | {data['bmi']['synthetic']:.1f} |
| HbA1c | {data['hba1c']['real']:.2f} | {data['hba1c']['synthetic']:.2f} |
| Insulin Use | {data['insulin_use']['real']:.4f} | {data['insulin_use']['synthetic']:.4f} |
| Gap Count (15m grid) | {data['gap_stats_15m']['real']['count']} | {data['gap_stats_15m']['synthetic']['count']} |
| Gap Median (min) | {data['gap_stats_15m']['real']['median']:.1f} | {data['gap_stats_15m']['synthetic']['median']:.1f} |
| Gap Mean (min) | {data['gap_stats_15m']['real']['mean']:.1f} | {data['gap_stats_15m']['synthetic']['mean']:.1f} |
| Gaps per 1000 slots | {data['gap_stats_15m']['real']['gaps_per_1000_slots']:.2f} | {data['gap_stats_15m']['synthetic']['gaps_per_1000_slots']:.2f} |
| Gaps per patient-day | {data['gap_stats_15m']['real']['gaps_per_patient_day']:.2f} | {data['gap_stats_15m']['synthetic']['gaps_per_patient_day']:.2f} |
| Share Missing Slots | {data['gap_stats_15m']['real']['share_missing_slots']:.4f} | {data['gap_stats_15m']['synthetic']['share_missing_slots']:.4f} |

## Metric-by-metric reading

### HbA1c Regression
For both cohorts:
- **Real Data**: patients used: {data['regression_hba1c_glucose']['real']['patients']}, handling of missing HbA1c: {data['regression_hba1c_glucose']['real']['missing_hba1c_handling']}. Regression slope: {data['regression_hba1c_glucose']['real']['slope']:.2f}, intercept: {data['regression_hba1c_glucose']['real']['intercept']:.2f}, R-squared: {data['regression_hba1c_glucose']['real']['r_squared']:.4f}. The glucose mean predicted by 28.7 x HbA1c - 46.7 is {data['regression_hba1c_glucose']['real']['predicted_mean_formula']:.2f} mg/dL, while the observed mean is {data['regression_hba1c_glucose']['real']['observed_mean']:.2f} mg/dL.
- **Synthetic Data**: patients used: {data['regression_hba1c_glucose']['synthetic']['patients']}, handling of missing HbA1c: {data['regression_hba1c_glucose']['synthetic']['missing_hba1c_handling']}. Regression slope: {data['regression_hba1c_glucose']['synthetic']['slope']:.2f}, intercept: {data['regression_hba1c_glucose']['synthetic']['intercept']:.2f}, R-squared: {data['regression_hba1c_glucose']['synthetic']['r_squared']:.4f}. The glucose mean predicted by 28.7 x HbA1c - 46.7 is {data['regression_hba1c_glucose']['synthetic']['predicted_mean_formula']:.2f} mg/dL, while the observed mean is {data['regression_hba1c_glucose']['synthetic']['observed_mean']:.2f} mg/dL.

**Observation**: At the real cohort's mean HbA1c, the formula 28.7 x HbA1c - 46.7 gives about {data['regression_hba1c_glucose']['real']['predicted_mean_formula']:.0f} mg/dL, while the observed mean glucose is about {data['regression_hba1c_glucose']['real']['observed_mean']:.0f} mg/dL. Possible hypotheses for this discrepancy (which need checking against the dataset paper) could include:
- The CGM device calibration or interstitial delay may systematically underreport true blood glucose.
- The sampled days may not be representative of the previous 3 months (e.g. patients improved diet when put on monitors).
- Severe missingness during high-glucose periods.

![HbA1c Regression](hba1c_scatter.png)

### Hour-of-Day Glucose Profile
![Hour of day mean glucose comparison](hour_profile_comparison.png)

## Changes a new synthetic cohort needs
"""
    for i, c in enumerate(changes):
        md += f"{i+1}. **{c['name']}**: {c['desc']}\n"
        
    with open('docs/REALISM.md', 'w') as f:
        f.write(md)
    print("Built REALISM.md")

if __name__ == '__main__':
    build_md()
