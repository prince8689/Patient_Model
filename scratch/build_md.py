import json

def build():
    with open('reports/realism_comparison.json', 'r') as f:
        data = json.load(f)
        
    md = f"""# Realism Comparison

This document compares the synthetic cohort against the real data (Shanghai T2DM dataset).

## Counts
| Metric | Real | Synthetic |
|---|---|---|
| Patients | {data['patients']['real']} | {data['patients']['synthetic']} |
| Recordings | {data['recordings']['real']} | {data['recordings']['synthetic']} |
| Observed Samples | {data['observed_samples']['real']} | {data['observed_samples']['synthetic']} |
| Total Slots | {data['total_slots']['real']} | {data['total_slots']['synthetic']} |

## Metrics Table

| Metric | Real | Synthetic | Distance |
|---|---|---|---|
| Mean Glucose (mg/dL) | {data['mean_glucose']['real']:.2f} | {data['mean_glucose']['synthetic']:.2f} | {abs(data['mean_glucose']['real'] - data['mean_glucose']['synthetic']):.2f} |
| Std Glucose (mg/dL) | {data['std_glucose']['real']:.2f} | {data['std_glucose']['synthetic']:.2f} | {abs(data['std_glucose']['real'] - data['std_glucose']['synthetic']):.2f} |
| CV Glucose | {data['cv_glucose']['real']:.4f} | {data['cv_glucose']['synthetic']:.4f} | {abs(data['cv_glucose']['real'] - data['cv_glucose']['synthetic']):.4f} |
| Time Below 70 (%) | {data['time_below_70']['real']:.4f} | {data['time_below_70']['synthetic']:.4f} | {abs(data['time_below_70']['real'] - data['time_below_70']['synthetic']):.4f} |
| Time 70-180 (%) | {data['time_70_180']['real']:.4f} | {data['time_70_180']['synthetic']:.4f} | {abs(data['time_70_180']['real'] - data['time_70_180']['synthetic']):.4f} |
| Time Above 180 (%) | {data['time_above_180']['real']:.4f} | {data['time_above_180']['synthetic']:.4f} | {abs(data['time_above_180']['real'] - data['time_above_180']['synthetic']):.4f} |
| Label Prevalence | {data['label_prevalence']['real']:.4f} | {data['label_prevalence']['synthetic']:.4f} | {abs(data['label_prevalence']['real'] - data['label_prevalence']['synthetic']):.4f} |
| Age | {data['age']['real']:.1f} | {data['age']['synthetic']:.1f} | {abs(data['age']['real'] - data['age']['synthetic']):.1f} |
| BMI | {data['bmi']['real']:.1f} | {data['bmi']['synthetic']:.1f} | {abs(data['bmi']['real'] - data['bmi']['synthetic']):.1f} |
| HbA1c | {data['hba1c']['real']:.2f} | {data['hba1c']['synthetic']:.2f} | {abs(data['hba1c']['real'] - data['hba1c']['synthetic']):.2f} |
| Insulin Use | {data['insulin_use']['real']:.4f} | {data['insulin_use']['synthetic']:.4f} | {abs(data['insulin_use']['real'] - data['insulin_use']['synthetic']):.4f} |
| Meal Rise (mg/dL) | {data['meal_rise_mean']['real']} | {data['meal_rise_mean']['synthetic']:.2f} | N/A |
| Gap Count (15m grid) | {data['gap_stats_15m']['real']['count']} | {data['gap_stats_15m']['synthetic']['count']} | {abs(data['gap_stats_15m']['real']['count'] - data['gap_stats_15m']['synthetic']['count'])} |
| Gap Median (15m grid, min) | {data['gap_stats_15m']['real']['median']:.1f} | {data['gap_stats_15m']['synthetic']['median']:.1f} | {abs(data['gap_stats_15m']['real']['median'] - data['gap_stats_15m']['synthetic']['median']):.1f} |
| Gap Mean (15m grid, min) | {data['gap_stats_15m']['real']['mean']:.1f} | {data['gap_stats_15m']['synthetic']['mean']:.1f} | {abs(data['gap_stats_15m']['real']['mean'] - data['gap_stats_15m']['synthetic']['mean']):.1f} |
| Gaps per 1000 slots | {data['gap_stats_15m']['real']['gaps_per_1000_slots']:.2f} | {data['gap_stats_15m']['synthetic']['gaps_per_1000_slots']:.2f} | {abs(data['gap_stats_15m']['real']['gaps_per_1000_slots'] - data['gap_stats_15m']['synthetic']['gaps_per_1000_slots']):.2f} |
| Gaps per patient-day | {data['gap_stats_15m']['real']['gaps_per_patient_day']:.2f} | {data['gap_stats_15m']['synthetic']['gaps_per_patient_day']:.2f} | {abs(data['gap_stats_15m']['real']['gaps_per_patient_day'] - data['gap_stats_15m']['synthetic']['gaps_per_patient_day']):.2f} |
| Share Missing Slots | {data['gap_stats_15m']['real']['share_missing_slots']:.4f} | {data['gap_stats_15m']['synthetic']['share_missing_slots']:.4f} | {abs(data['gap_stats_15m']['real']['share_missing_slots'] - data['gap_stats_15m']['synthetic']['share_missing_slots']):.4f} |
| Regression Slope (HbA1c to mean glucose) | {data['regression_hba1c_glucose']['real']['slope']:.2f} | {data['regression_hba1c_glucose']['synthetic']['slope']:.2f} | {abs(data['regression_hba1c_glucose']['real']['slope'] - data['regression_hba1c_glucose']['synthetic']['slope']):.2f} |
| Regression Intercept | {data['regression_hba1c_glucose']['real']['intercept']:.2f} | {data['regression_hba1c_glucose']['synthetic']['intercept']:.2f} | {abs(data['regression_hba1c_glucose']['real']['intercept'] - data['regression_hba1c_glucose']['synthetic']['intercept']):.2f} |
| Regression R-squared | {data['regression_hba1c_glucose']['real']['r_squared']:.4f} | {data['regression_hba1c_glucose']['synthetic']['r_squared']:.4f} | {abs(data['regression_hba1c_glucose']['real']['r_squared'] - data['regression_hba1c_glucose']['synthetic']['r_squared']):.4f} |

## Hour of Day Profile

![Hour of day mean glucose comparison](hour_profile_comparison.png)

## Required Changes for a New Synthetic Cohort

To improve realism, a new synthetic cohort needs:
1. Target mean glucose must be closer to {data['mean_glucose']['real']:.1f} mg/dL, and time above 180 should be reduced from {data['time_above_180']['synthetic']*100:.1f}% to match the observed {data['time_above_180']['real']*100:.1f}%.
2. The HbA1c to mean glucose relationship needs flattening. The real slope is {data['regression_hba1c_glucose']['real']['slope']:.2f} compared to synthetic {data['regression_hba1c_glucose']['synthetic']['slope']:.2f}.
3. The average BMI in the real cohort is {data['bmi']['real']:.1f}, which is {abs(data['bmi']['real'] - data['bmi']['synthetic']):.1f} different from synthetic.
4. The average age is {data['age']['real']:.1f} years.
5. The insulin usage should be closer to {data['insulin_use']['real']*100:.1f}%.
6. The gap generation needs fewer but longer sensor outages (real gaps per 1000 slots: {data['gap_stats_15m']['real']['gaps_per_1000_slots']:.2f}, synthetic: {data['gap_stats_15m']['synthetic']['gaps_per_1000_slots']:.2f}).
"""
    with open('docs/REALISM.md', 'w') as f:
        f.write(md)
        
    print("Markdown rebuilt.")
    
    import matplotlib.pyplot as plt
    real_h = data['hour_profile']['real']
    syn_h = data['hour_profile']['synthetic']
    
    plt.figure(figsize=(10, 6))
    plt.plot(list(map(int, real_h.keys())), list(real_h.values()), label='Real', marker='o')
    plt.plot(list(map(int, syn_h.keys())), list(syn_h.values()), label='Synthetic', marker='x')
    plt.title('Hour-of-Day Mean Glucose')
    plt.xlabel('Hour')
    plt.ylabel('Mean Glucose (mg/dL)')
    plt.legend()
    plt.grid(True)
    plt.savefig('reports/hour_profile_comparison.png')
    
    # Scatter for HbA1c
    # We will generate this when we actually collect it, but we can't from JSON easily because JSON only has the regression stats.
    # Wait, the prompt says "a scatter figure of patient mean glucose against HbA1c for both cohorts".
    # I will have to plot this in Python using the actual data.

if __name__ == '__main__':
    build()
