import json
from pathlib import Path

def main():
    with open('reports/realism_comparison.json', 'r') as f:
        data = json.load(f)

    md = []
    md.append("# Realism Comparison")
    md.append("\nThis document compares the synthetic cohort against the real data (Shanghai T2DM dataset).")
    
    md.append("\n## Metrics Table")
    md.append("| Metric | Real | Synthetic |")
    md.append("|---|---|---|")
    
    # Counts
    md.append(f"| Patients | {data['patients']['real']} | {data['patients']['synthetic']} |")
    md.append(f"| Recordings | {data['recordings']['real']} | {data['recordings']['synthetic']} |")
    md.append(f"| Observed Samples | {data['observed_samples']['real']} | {data['observed_samples']['synthetic']} |")
    md.append(f"| Total Slots | {data['total_slots']['real']} | {data['total_slots']['synthetic']} |")
    
    # Glucose distribution
    md.append(f"| Mean Glucose (mg/dL) | {data['mean_glucose']['real']:.2f} | {data['mean_glucose']['synthetic']:.2f} |")
    md.append(f"| Std Glucose (mg/dL) | {data['std_glucose']['real']:.2f} | {data['std_glucose']['synthetic']:.2f} |")
    md.append(f"| CV Glucose | {data['cv_glucose']['real']:.4f} | {data['cv_glucose']['synthetic']:.4f} |")
    
    md.append(f"| Time Below 70 (%) | {data['time_below_70']['real']:.4f} | {data['time_below_70']['synthetic']:.4f} |")
    md.append(f"| Time 70-180 (%) | {data['time_70_180']['real']:.4f} | {data['time_70_180']['synthetic']:.4f} |")
    md.append(f"| Time Above 180 (%) | {data['time_above_180']['real']:.4f} | {data['time_above_180']['synthetic']:.4f} |")
    
    md.append(f"| Label Prevalence | {data['label_prevalence']['real']:.4f} | {data['label_prevalence']['synthetic']:.4f} |")
    
    # Demographics
    md.append(f"| Age | {data['age']['real']:.1f} | {data['age']['synthetic']:.1f} |")
    md.append(f"| BMI | {data['bmi']['real']:.1f} | {data['bmi']['synthetic']:.1f} |")
    md.append(f"| HbA1c | {data['hba1c']['real']:.2f} | {data['hba1c']['synthetic']:.2f} |")
    md.append(f"| Insulin Use | {data['insulin_use']['real']:.4f} | {data['insulin_use']['synthetic']:.4f} |")
    
    # Gap Stats
    real_gaps = data['gap_stats_15m']['real']
    syn_gaps = data['gap_stats_15m']['synthetic']
    md.append(f"| Gap Count (15m grid) | {real_gaps['count']} | {syn_gaps['count']} |")
    md.append(f"| Gap Median (min) | {real_gaps['median']:.1f} | {syn_gaps['median']:.1f} |")
    md.append(f"| Gap Mean (min) | {real_gaps['mean']:.1f} | {syn_gaps['mean']:.1f} |")
    md.append(f"| Gaps per 1000 slots | {real_gaps['gaps_per_1000_slots']:.2f} | {syn_gaps['gaps_per_1000_slots']:.2f} |")
    md.append(f"| Gaps per patient-day | {real_gaps['gaps_per_patient_day']:.2f} | {syn_gaps['gaps_per_patient_day']:.2f} |")
    md.append(f"| Share Missing Slots | {real_gaps['share_missing_slots']:.4f} | {syn_gaps['share_missing_slots']:.4f} |")

    # Meal Rise
    md.append(f"| Meal Rise (mg/dL) | {data['meal_rise_mean']['real']} | {data['meal_rise_mean']['synthetic']:.2f} |")
    
    md.append("\n## Metric-by-metric reading")
    
    md.append("\n### HbA1c Regression")
    
    r_reg = data['regression_hba1c_glucose']['real']
    s_reg = data['regression_hba1c_glucose']['synthetic']
    
    md.append("For both cohorts:")
    md.append(f"- **Real Data**: patients used: {r_reg['patients']}, handling of missing HbA1c: {r_reg['missing_hba1c_handling']}. Regression slope: {r_reg['slope']:.2f}, intercept: {r_reg['intercept']:.2f}, R-squared: {r_reg['r_squared']:.4f}. The glucose mean predicted by 28.7 x HbA1c - 46.7 is {r_reg['predicted_mean_formula']:.2f} mg/dL, while the observed mean is {r_reg['observed_mean']:.2f} mg/dL.")
    md.append(f"- **Synthetic Data**: patients used: {s_reg['patients']}, handling of missing HbA1c: {s_reg['missing_hba1c_handling']}. Regression slope: {s_reg['slope']:.2f}, intercept: {s_reg['intercept']:.2f}, R-squared: {s_reg['r_squared']:.4f}. The glucose mean predicted by 28.7 x HbA1c - 46.7 is {s_reg['predicted_mean_formula']:.2f} mg/dL, while the observed mean is {s_reg['observed_mean']:.2f} mg/dL.")
    md.append("\n![HbA1c Regression](hba1c_scatter.png)")
    
    md.append("\n### Hour-of-Day Glucose Profile")
    md.append("![Hour of day mean glucose comparison](hour_profile_comparison.png)")
    
    md.append("\n## Changes a new synthetic cohort needs")
    md.append("1. Mean Glucose and Time Above 180: The synthetic mean glucose (219.30) is 78.20 mg/dL higher than real (141.10). Time above 180 must drop from 0.6861 to 0.1962.")
    md.append("2. Gap Statistics: Synthetic gaps per 1000 slots (16.88) are significantly higher than real (0.68). The generation should produce fewer gaps, but with a longer median length (currently 15.0 vs 30.0 mins).")
    md.append("3. HbA1c to Mean Glucose Regression: The synthetic slope (42.94) is much steeper than the real cohort (5.86). The generator should flatten this relationship.")
    md.append("4. Demographics: BMI should be shifted closer to 24.1 (currently 29.7). Age should increase slightly to 60.2 (currently 54.6). Insulin usage should increase from 0.2250 to 0.3200.")
    md.append("5. Missing Meal Markers: The synthetic data generates precise meal rises, whereas real data lacks exact meal timestamps.")
    
    with open('docs/REALISM.md', 'w') as f:
        f.write('\n'.join(md))
        
if __name__ == '__main__':
    main()
