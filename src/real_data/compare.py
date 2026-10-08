import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from scipy.stats import linregress

def gap_statistics(df, grid_minutes, group_col='patient_id'):
    """Compute gap statistics using the unified gaps module."""
    from src.real_data.gaps import compute_slots_and_gaps
    
    gaps = []
    total_slots = 0
    observed_samples = 0
    
    for _, group in df.groupby(group_col):
        obs = group.dropna(subset=['glucose_mgdl'])
        if obs.empty: continue
        
        ts = obs['timestamp']
        slots, missing, g = compute_slots_and_gaps(ts, grid_minutes)
        total_slots += slots
        observed_samples += len(ts)
        gaps.extend(g)
        
    return {
        "count": len(gaps),
        "median": float(np.median(gaps)) if gaps else 0.0,
        "mean": float(np.mean(gaps)) if gaps else 0.0,
        "unit": "minutes",
        "observed_samples": observed_samples,
        "total_slots": total_slots,
        "gaps_per_1000_slots": float(len(gaps) * 1000 / total_slots) if total_slots else 0.0,
        "gaps_per_patient_day": float(len(gaps) / (total_slots * grid_minutes / 1440.0)) if total_slots else 0.0,
        "share_missing_slots": float((total_slots - observed_samples) / total_slots) if total_slots else 0.0
    }

def meal_rise(df, meal_times):
    """Compute meal rise over next 120 minutes."""
    rises = []
    for _, row in meal_times.iterrows():
        pid = row['patient_id']
        ts = row['timestamp']
        future = df[(df['patient_id'] == pid) & 
                    (df['timestamp'] >= ts) & 
                    (df['timestamp'] <= ts + pd.Timedelta(minutes=120))]
        if not future.empty:
            base = future.iloc[0]['glucose_mgdl']
            peak = future['glucose_mgdl'].max()
            if not np.isnan(base) and not np.isnan(peak):
                rises.append(peak - base)
    
    if rises:
        return float(np.mean(rises))
    return float('nan')

def compute_cohort_metrics(df, prof_df, group_col):
    obs = df.dropna(subset=['glucose_mgdl'])
    
    # Patient level stats
    pat_stats = obs.groupby('patient_id')['glucose_mgdl'].agg(['mean', 'std']).reset_index()
    pat_stats['cv'] = pat_stats['std'] / pat_stats['mean']
    
    # Time in ranges
    def tir(g):
        tbr = (g < 70).mean()
        tar = (g > 180).mean()
        tir = ((g >= 70) & (g <= 180)).mean()
        return pd.Series({'tbr': tbr, 'tir': tir, 'tar': tar})
    
    ranges = obs.groupby('patient_id')['glucose_mgdl'].apply(tir).unstack().reset_index()
    pat_stats = pat_stats.merge(ranges, on='patient_id')
    
    # Hour of day
    obs['hour'] = obs['timestamp'].dt.hour
    hour_profile = obs.groupby('hour')['glucose_mgdl'].mean().to_dict()
    
    # Merge profiles
    pat_stats = pat_stats.merge(prof_df, on='patient_id', how='left')
    
    return {
        "mean_glucose": float(pat_stats['mean'].mean()),
        "std_glucose": float(pat_stats['std'].mean()),
        "cv_glucose": float(pat_stats['cv'].mean()),
        "time_below_70": float(pat_stats['tbr'].mean()),
        "time_70_180": float(pat_stats['tir'].mean()),
        "time_above_180": float(pat_stats['tar'].mean()),
        "age": float(pat_stats['age'].mean()),
        "bmi": float(pat_stats['bmi'].mean()),
        "hba1c": float(pat_stats['hba1c'].mean()),
        "insulin_use": float(pat_stats['use_insulin'].mean() if 'use_insulin' in pat_stats else pat_stats['on_insulin'].mean()),
        "hour_profile": {str(k): float(v) for k, v in hour_profile.items()},
        "label_prevalence": float(df['label'].mean()) if 'label' in df.columns else None
    }

def compare():
    print("Synth...")
    sp = pd.read_csv("data/raw/patients.csv")
    sg = pd.read_csv("data/raw/wearable.csv")
    sg['timestamp'] = pd.to_datetime(sg['timestamp'], format='mixed')
    sg = sg.sort_values(['patient_id', 'timestamp'])
    
    synth_gaps_5m = gap_statistics(sg, 5, 'patient_id')
    
    sg_third = sg.iloc[::3].copy()
    synth_gaps_15m = gap_statistics(sg_third, 15, 'patient_id')
    
    synth_meals = sg[sg['meal_carbs_g'] > 0][['patient_id', 'timestamp']].copy()
    synth_meal_rise = meal_rise(sg, synth_meals)
    
    print("Real...")
    rp = pd.read_csv("data/processed/real_profiles.csv")
    rg = pd.read_csv("data/processed/real_glucose.csv")
    rg['timestamp'] = pd.to_datetime(rg['timestamp'], format='mixed')
    rg = rg.sort_values(['patient_id', 'timestamp'])
    
    real_gaps_15m = gap_statistics(rg, 15, 'recording_id')
    
    real_meals_csv = pd.read_csv("data/processed/real_meals.csv")
    
    metrics = {
        "patients": {"real": int(rg['patient_id'].nunique()), "synthetic": int(sg_third['patient_id'].nunique()), "real_previous": 87},
        "recordings": {"real": int(rg['recording_id'].nunique()), "synthetic": int(sg_third['patient_id'].nunique())},
        "observed_samples": {"real": real_gaps_15m['observed_samples'], "synthetic": synth_gaps_15m['observed_samples']},
        "total_slots": {"real": real_gaps_15m['total_slots'], "synthetic": synth_gaps_15m['total_slots']},
        "gap_stats_15m": {
            "real": {
                "count": real_gaps_15m['count'],
                "median": real_gaps_15m['median'],
                "mean": real_gaps_15m['mean'],
                "gaps_per_1000_slots": real_gaps_15m['gaps_per_1000_slots'],
                "gaps_per_patient_day": real_gaps_15m['gaps_per_patient_day'],
                "share_missing_slots": real_gaps_15m['share_missing_slots']
            },
            "synthetic": {
                "count": synth_gaps_15m['count'],
                "median": synth_gaps_15m['median'],
                "mean": synth_gaps_15m['mean'],
                "gaps_per_1000_slots": synth_gaps_15m['gaps_per_1000_slots'],
                "gaps_per_patient_day": synth_gaps_15m['gaps_per_patient_day'],
                "share_missing_slots": synth_gaps_15m['share_missing_slots']
            }
        },
        "gap_stats_5m": {
            "synthetic": {
                "count": synth_gaps_5m['count'],
                "median": synth_gaps_5m['median'],
                "mean": synth_gaps_5m['mean'],
                "gaps_per_1000_slots": synth_gaps_5m['gaps_per_1000_slots'],
                "gaps_per_patient_day": synth_gaps_5m['gaps_per_patient_day'],
                "share_missing_slots": synth_gaps_5m['share_missing_slots']
            }
        },
        "meal_rise_mean": {"real": "not computable on real data: no exact meal timestamp exists. Raw meal fields: " + str(real_meals_csv.columns.tolist()), "synthetic": synth_meal_rise},
    }
    
    # Compute full cohort metrics
    real_metrics = compute_cohort_metrics(rg, rp, 'patient_id')
    synth_metrics = compute_cohort_metrics(sg_third, sp, 'patient_id')
    
    # Read synthetic labels to compute prevalence properly
    sl = pd.read_csv("data/processed/labels.csv")
    synth_metrics['label_prevalence'] = float(sl['spike_next_2h'].mean())
    
    for k in real_metrics:
        metrics[k] = {"real": real_metrics[k], "synthetic": synth_metrics[k]}
    
    # Regression
    real_pat_g = rg.dropna(subset=['glucose_mgdl']).groupby('patient_id')['glucose_mgdl'].mean().reset_index()
    real_pat_g = real_pat_g.merge(rp[['patient_id', 'hba1c']], on='patient_id').dropna(subset=['hba1c', 'glucose_mgdl'])
    rr = linregress(real_pat_g['hba1c'], real_pat_g['glucose_mgdl'])
    
    synth_pat_g = sg_third.dropna(subset=['glucose_mgdl']).groupby('patient_id')['glucose_mgdl'].mean().reset_index()
    synth_pat_g = synth_pat_g.merge(sp[['patient_id', 'hba1c']], on='patient_id').dropna(subset=['hba1c', 'glucose_mgdl'])
    sr = linregress(synth_pat_g['hba1c'], synth_pat_g['glucose_mgdl'])
    
    metrics["regression_hba1c_glucose"] = {
        "real": {
            "patients": len(real_pat_g),
            "missing_hba1c_handling": "dropped",
            "slope": float(rr.slope),
            "intercept": float(rr.intercept),
            "r_squared": float(rr.rvalue**2),
            "predicted_mean_formula": float(28.7 * real_pat_g['hba1c'].mean() - 46.7),
            "observed_mean": float(real_pat_g['glucose_mgdl'].mean())
        },
        "synthetic": {
            "patients": len(synth_pat_g),
            "missing_hba1c_handling": "dropped",
            "slope": float(sr.slope),
            "intercept": float(sr.intercept),
            "r_squared": float(sr.rvalue**2),
            "predicted_mean_formula": float(28.7 * synth_pat_g['hba1c'].mean() - 46.7),
            "observed_mean": float(synth_pat_g['glucose_mgdl'].mean())
        }
    }
    
    # Scatter plot
    plt.figure(figsize=(8, 6))
    plt.scatter(real_pat_g['hba1c'], real_pat_g['glucose_mgdl'], label='Real', alpha=0.6)
    plt.scatter(synth_pat_g['hba1c'], synth_pat_g['glucose_mgdl'], label='Synthetic', alpha=0.6)
    plt.xlabel('HbA1c')
    plt.ylabel('Patient Mean Glucose (mg/dL)')
    plt.title('Patient Mean Glucose vs HbA1c')
    plt.legend()
    plt.grid(True)
    plt.savefig('reports/hba1c_scatter.png')
    plt.close()

    
    with open("reports/realism_comparison.json", "w") as f:
        json.dump(metrics, f, indent=4)
        
    print("Saved realism_comparison.json.")
    print("Real meal evidence:")
    print(real_meals_csv.columns.tolist())
    print(real_meals_csv[['dietary_intake_text']].head(2).to_dict())

if __name__ == "__main__":
    compare()
