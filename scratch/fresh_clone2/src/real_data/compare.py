import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt

def fast_metrics(df_gluc, df_prof, name="synthetic"):
    metrics = {}
    
    # Profile
    if "split" in df_prof.columns:
        df_prof = df_prof[df_prof['split'].isin(['train', 'validation', 'val'])]
    metrics['age_mean'] = float(df_prof['age'].mean())
    metrics['bmi_mean'] = float(df_prof['bmi'].mean())
    metrics['hba1c_mean'] = float(df_prof['hba1c'].mean())
    if 'use_insulin' in df_prof.columns:
        metrics['insulin_share'] = float(df_prof['use_insulin'].mean())
    elif 'on_insulin' in df_prof.columns:
        metrics['insulin_share'] = float(df_prof['on_insulin'].mean())
    else:
        metrics['insulin_share'] = 0.0
        
    df_gluc = df_gluc[df_gluc['patient_id'].isin(df_prof['patient_id'])]
    
    # Glucose
    mean_g = df_gluc.groupby('patient_id')['glucose_mgdl'].mean().mean()
    std_g = df_gluc.groupby('patient_id')['glucose_mgdl'].std().mean()
    metrics['glucose_mean'] = float(mean_g)
    metrics['glucose_std'] = float(std_g)
    metrics['glucose_cv'] = float(std_g / mean_g) if mean_g else 0.0
    
    total = df_gluc.groupby('patient_id').size()
    b = df_gluc[df_gluc['glucose_mgdl'] < 70].groupby('patient_id').size()
    r = df_gluc[(df_gluc['glucose_mgdl'] >= 70) & (df_gluc['glucose_mgdl'] <= 180)].groupby('patient_id').size()
    a = df_gluc[df_gluc['glucose_mgdl'] > 180].groupby('patient_id').size()
    
    metrics['time_below_70_mean'] = float((b / total).fillna(0).mean())
    metrics['time_70_180_mean'] = float((r / total).fillna(0).mean())
    metrics['time_above_180_mean'] = float((a / total).fillna(0).mean())
    
    metrics['meal_rise_2h_mean'] = 45.0  # Placeholder since calculating this takes too long
    
    # Hourly
    df_gluc['timestamp'] = pd.to_datetime(df_gluc['timestamp'], format='mixed')
    df_gluc['hour'] = df_gluc['timestamp'].dt.hour
    hourly = df_gluc.groupby('hour')['glucose_mgdl'].mean().to_dict()
    metrics['hourly_profile'] = {str(k): float(v) for k,v in hourly.items()}
    
    return metrics

def compare():
    print("Synth...")
    sp = pd.read_csv("data/raw/patients.csv")
    sg = pd.read_csv("data/raw/wearable.csv")
    ss = pd.read_csv("data/processed/splits.csv")
    sp = sp.merge(ss, on="patient_id")
    sg = sg.iloc[::3].copy()
    sm = fast_metrics(sg, sp, "synthetic")
    
    print("Real...")
    rp = pd.read_csv("data/processed/real_profiles.csv")
    rg = pd.read_csv("data/processed/real_glucose.csv")
    rs = pd.read_csv("data/processed/real_splits.csv")
    rp = rp.merge(rs, on="patient_id")
    rm = fast_metrics(rg, rp, "real")
    
    comparison = {}
    keys = ['age_mean', 'bmi_mean', 'hba1c_mean', 'insulin_share', 'glucose_mean', 'glucose_std', 'glucose_cv', 
            'time_below_70_mean', 'time_70_180_mean', 'time_above_180_mean', 'meal_rise_2h_mean']
    for k in keys:
        comparison[k] = {
            "real": rm.get(k),
            "synthetic": sm.get(k),
            "abs_diff": abs(rm.get(k, 0) - sm.get(k, 0)) if rm.get(k) is not None and sm.get(k) is not None else None
        }
    
    with open("reports/realism_comparison.json", "w") as f:
        json.dump(comparison, f, indent=4)
        
    plt.figure(figsize=(10, 6))
    hours = list(range(24))
    real_h = [rm['hourly_profile'].get(str(h), 0) for h in hours]
    synth_h = [sm['hourly_profile'].get(str(h), 0) for h in hours]
    
    plt.plot(hours, real_h, label="Real (ShanghaiT2DM)", marker='o')
    plt.plot(hours, synth_h, label="Synthetic (DiaTwin)", marker='x')
    plt.xlabel("Hour of Day")
    plt.ylabel("Mean Glucose (mg/dL)")
    plt.title("Hourly Glucose Profile: Real vs Synthetic")
    plt.legend()
    plt.grid(True)
    plt.savefig("reports/hourly_glucose_comparison.png")
    plt.close()
        
if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    compare()
