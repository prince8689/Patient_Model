import pandas as pd
import numpy as np
import json
from pathlib import Path
from sklearn.linear_model import LinearRegression

def compute_gap_stats(timestamps_series):
    diffs = timestamps_series.diff().dt.total_seconds() / 60.0
    gaps = diffs[diffs > 16].dropna()
    if len(gaps) == 0:
        return {"median_gap_min": 0.0, "mean_gap_min": 0.0, "gap_count": 0}
    return {
        "median_gap_min": float(gaps.median()),
        "mean_gap_min": float(gaps.mean()),
        "gap_count": int(len(gaps))
    }

def process():
    # Load Synthetic
    syn_prof = pd.read_csv("data/raw/patients.csv")
    syn_cgm = pd.read_csv("data/raw/wearable.csv")
    
    syn_cgm['timestamp'] = pd.to_datetime(syn_cgm['timestamp'])
    
    # Load Real
    real_prof = pd.read_csv("data/processed/real_profiles.csv")
    real_cgm = pd.read_csv("data/processed/real_glucose.csv")
    real_cgm['timestamp'] = pd.to_datetime(real_cgm['timestamp'])
    
    results = {}
    
    # Use insulin
    results["synthetic_use_insulin"] = float(syn_prof['on_insulin'].mean())
    results["real_use_insulin"] = float(real_prof['use_insulin'].mean())
    
    # Load synthetic labels
    syn_labels = pd.read_csv("data/processed/labels.csv")
    
    # Label prevalence
    results["synthetic_label_prevalence"] = float(syn_labels['spike_next_2h'].mean())
    results["real_label_prevalence"] = float(real_cgm['label'].mean())
    
    # Meal rise (only computable for synthetic due to lack of exact meal carbs/times in real)
    meal_rises = []
    meals_only = syn_cgm[syn_cgm['meal_carbs_g'] > 0]
    for _, meal in meals_only.iterrows():
        t_meal = meal['timestamp']
        pid = meal['patient_id']
        cgm_pat = syn_cgm[syn_cgm['patient_id'] == pid]
        
        pre = cgm_pat[(cgm_pat['timestamp'] <= t_meal) & (cgm_pat['timestamp'] >= t_meal - pd.Timedelta(minutes=30))]['glucose_mgdl'].dropna()
        post = cgm_pat[(cgm_pat['timestamp'] > t_meal) & (cgm_pat['timestamp'] <= t_meal + pd.Timedelta(hours=2))]['glucose_mgdl'].dropna()
        
        if not pre.empty and not post.empty:
            rise = post.max() - pre.mean()
            meal_rises.append(rise)
            
    results["synthetic_meal_rise_mean"] = float(np.mean(meal_rises))
    results["real_meal_rise_mean"] = "not computable on real data: no quantified exact meal timestamps"
    
    # The synthetic side uses every third sample of the synthetic data to match 15m real grid
    syn_cgm_15m = syn_cgm.iloc[::3].copy()
    
    # Gap stats - Synthetic (5m and 15m grids)
    # Gaps are defined as runs of missing values or absent slots
    def get_gap_lengths(df, freq_min):
        gaps = []
        for pid, group in df.groupby("patient_id"):
            group = group.sort_values("timestamp")
            
            # Find missing value gaps
            is_na = group['glucose_mgdl'].isna()
            gap_blocks = is_na.ne(is_na.shift()).cumsum()
            na_runs = is_na.groupby(gap_blocks).sum()
            na_runs = na_runs[na_runs > 0]
            for run_len in na_runs:
                gaps.append(run_len * freq_min)
                
            # Find timestamp gaps
            diffs = group["timestamp"].diff().dt.total_seconds() / 60.0
            ts_gaps = diffs[diffs > (freq_min + 1)].dropna()
            gaps.extend((ts_gaps - freq_min).tolist())
            
        return gaps
        
    syn_gaps_5m = get_gap_lengths(syn_cgm, 5)
    syn_gaps_15m = get_gap_lengths(syn_cgm_15m, 15)
        
    # Real gap stats (already 15m)
    real_gaps = []
    for rid, group in real_cgm.groupby("recording_id"):
        group = group.sort_values("timestamp")
        diffs = group["timestamp"].diff().dt.total_seconds() / 60.0
        real_gaps.extend(diffs[diffs > 16].dropna().tolist())
        
    results["synthetic_gaps"] = {
        "5m_grid": {
            "median_min": float(np.median(syn_gaps_5m)) if syn_gaps_5m else 0.0,
            "mean_min": float(np.mean(syn_gaps_5m)) if syn_gaps_5m else 0.0,
            "count": len(syn_gaps_5m)
        },
        "15m_grid": {
            "median_min": float(np.median(syn_gaps_15m)) if syn_gaps_15m else 0.0,
            "mean_min": float(np.mean(syn_gaps_15m)) if syn_gaps_15m else 0.0,
            "count": len(syn_gaps_15m)
        }
    }
    
    results["real_gaps"] = {
        "median_min": float(np.median(real_gaps)) if real_gaps else 0.0,
        "mean_min": float(np.mean(real_gaps)) if real_gaps else 0.0,
        "count": len(real_gaps)
    }
    
    # Counts
    results["synthetic_counts"] = {
        "samples": len(syn_cgm_15m),
        "patients": syn_prof['patient_id'].nunique(),
        "recordings": syn_prof['patient_id'].nunique()
    }
    
    results["real_counts"] = {
        "samples": len(real_cgm),
        "patients": real_prof['patient_id'].nunique(),
        "recordings": real_cgm['recording_id'].nunique()
    }
    
    # Regression of patient mean glucose on HbA1c
    # Synthetic
    syn_mean = syn_cgm_15m.groupby("patient_id")['glucose_mgdl'].mean().reset_index()
    syn_reg = syn_prof[['patient_id', 'hba1c']].merge(syn_mean, on="patient_id").dropna()
    X_syn = syn_reg[['hba1c']].values
    y_syn = syn_reg['glucose_mgdl'].values
    if len(X_syn) > 1:
        reg = LinearRegression().fit(X_syn, y_syn)
        results["synthetic_regression"] = {
            "patients": len(X_syn),
            "slope": float(reg.coef_[0]),
            "intercept": float(reg.intercept_),
            "r_squared": float(reg.score(X_syn, y_syn))
        }
        
    # Real
    real_mean = real_cgm.groupby("patient_id")['glucose_mgdl'].mean().reset_index()
    real_reg = real_prof[['patient_id', 'hba1c']].merge(real_mean, on="patient_id").dropna()
    X_real = real_reg[['hba1c']].values
    y_real = real_reg['glucose_mgdl'].values
    if len(X_real) > 1:
        reg = LinearRegression().fit(X_real, y_real)
        results["real_regression"] = {
            "patients": len(X_real),
            "slope": float(reg.coef_[0]),
            "intercept": float(reg.intercept_),
            "r_squared": float(reg.score(X_real, y_real))
        }

    with open("reports/realism_comparison.json", "w") as f:
        json.dump(results, f, indent=4)
        
if __name__ == "__main__":
    process()
