import pandas as pd
import numpy as np
import os
import json
import hashlib
import yaml
from pathlib import Path
from sklearn.model_selection import train_test_split

def load_config() -> dict:
    """Load the real data configuration."""
    with open("configs/real_data.yaml", "r") as f:
        return yaml.safe_load(f)

def harmonize_shanghai_t2dm():
    """Harmonize the ShanghaiT2DM dataset."""
    config = load_config()
    raw_dir = Path(config["data_path"])
    out_dir = Path(config["processed_path"])
    out_dir.mkdir(parents=True, exist_ok=True)
    
    summary_file = raw_dir / "Shanghai_T2DM_Summary.xlsx"
    data_folder = raw_dir / "Shanghai_T2DM"
    
    summary_df = pd.read_excel(summary_file, sheet_name="T2DM")
    
    profiles = []
    glucose_records = []
    meal_records = []
    
    missing_counts = {
        "age": 0, "sex": 0, "bmi": 0, "hba1c": 0, "diabetes_duration": 0,
        "use_insulin": 0, "use_metformin": 0, "hypertension": 0
    }
    
    gap_lengths = []
    duplicate_timestamps_total = 0
    impossible_glucose_total = 0
    total_glucose_samples = 0
    
    # Process profiles
    for _, row in summary_df.iterrows():
        pid = str(row['Patient Number'])
        
        # Profile extraction
        age = row.get('Age (years)', np.nan)
        gender_code = row.get('Gender (Female=1, Male=2)', np.nan)
        sex = "Female" if gender_code == 1 else ("Male" if gender_code == 2 else np.nan)
        bmi = row.get('BMI (kg/m2)', np.nan)
        
        hba1c_ifcc = row.get('HbA1c (mmol/mol)', np.nan)
        try:
            hba1c_ifcc = float(hba1c_ifcc)
        except (ValueError, TypeError):
            hba1c_ifcc = np.nan
        hba1c = (hba1c_ifcc / 10.929) + 2.15 if not pd.isna(hba1c_ifcc) else np.nan
        
        duration = row.get('Duration of diabetes (years)', np.nan)
        
        hypo_agents = str(row.get('Hypoglycemic Agents', '')).lower()
        use_insulin = 1 if "insulin" in hypo_agents else 0
        use_metformin = 1 if "metformin" in hypo_agents else 0
        
        comorbidities = str(row.get('Comorbidities', '')).lower()
        hypertension = 1 if "hypertension" in comorbidities else 0
        
        if pd.isna(age): missing_counts["age"] += 1
        if pd.isna(sex): missing_counts["sex"] += 1
        if pd.isna(bmi): missing_counts["bmi"] += 1
        if pd.isna(hba1c): missing_counts["hba1c"] += 1
        if pd.isna(duration): missing_counts["diabetes_duration"] += 1
        
        profiles.append({
            "patient_id": pid,
            "age": age,
            "sex": sex,
            "bmi": bmi,
            "hba1c": hba1c,
            "diabetes_duration": duration,
            "use_insulin": use_insulin,
            "use_metformin": use_metformin,
            "hypertension": hypertension
        })
        
        # Process timeseries
        file_path = data_folder / f"{pid}.xlsx"
        if not file_path.exists():
            # There is one typo in file names sometimes (e.g. .xls vs .xlsx), fallback to glob
            matching = list(data_folder.glob(f"{pid}.xls*"))
            if matching:
                file_path = matching[0]
            else:
                continue
                
        try:
            ts_df = pd.read_excel(file_path)
        except Exception:
            continue
            
        ts_df = ts_df.sort_values('Date').reset_index(drop=True)
        
        # Glucose
        cgm = ts_df[['Date', 'CGM (mg / dl)']].dropna().copy()
        cgm = cgm.rename(columns={'Date': 'timestamp', 'CGM (mg / dl)': 'glucose_mgdl'})
        
        dups = cgm.duplicated(subset=['timestamp']).sum()
        duplicate_timestamps_total += dups
        cgm = cgm.drop_duplicates(subset=['timestamp'])
        
        impossible = ((cgm['glucose_mgdl'] < 40) | (cgm['glucose_mgdl'] > 400)).sum()
        impossible_glucose_total += impossible
        cgm = cgm[(cgm['glucose_mgdl'] >= 40) & (cgm['glucose_mgdl'] <= 400)]
        
        total_glucose_samples += len(cgm)
        
        if len(cgm) > 1:
            diffs = cgm['timestamp'].diff().dt.total_seconds() / 60.0
            gaps = diffs[diffs > 16].tolist() # 15 min grid + 1 min tolerance
            gap_lengths.extend(gaps)
            
        # Compute labels
        # Horizon = 120 mins (8 steps), step = 15 mins
        horizon = config['labeling']['horizon_minutes']
        threshold = config['labeling']['threshold_mgdl']
        min_cov = config['labeling']['min_coverage_ratio']
        
        labels = []
        for i in range(len(cgm)):
            t_curr = cgm['timestamp'].iloc[i]
            val_curr = cgm['glucose_mgdl'].iloc[i]
            
            t_end = t_curr + pd.Timedelta(minutes=horizon)
            future = cgm[(cgm['timestamp'] > t_curr) & (cgm['timestamp'] <= t_end)]
            
            if len(future) >= (horizon / 15) * min_cov:
                max_future = future['glucose_mgdl'].max()
                label = 1 if max_future >= (val_curr + threshold) else 0
                labels.append(label)
            else:
                labels.append(np.nan)
                
        cgm['label'] = labels
        cgm['patient_id'] = pid
        cgm['recording_id'] = pid # 1:1 mapping in this dataset
        
        glucose_records.append(cgm)
        
        # Meals
        meals = ts_df[['Date', 'Dietary intake']].dropna().copy()
        for _, m_row in meals.iterrows():
            meal_records.append({
                "patient_id": pid,
                "recording_id": pid,
                "timestamp": m_row['Date'],
                "dietary_intake_text": str(m_row['Dietary intake']),
                "carbs_g": np.nan
            })

    prof_df = pd.DataFrame(profiles)
    gluc_df = pd.concat(glucose_records, ignore_index=True)
    meal_df = pd.DataFrame(meal_records)
    
    # Save CSVs
    prof_df.to_csv(out_dir / "real_profiles.csv", index=False)
    gluc_df.to_csv(out_dir / "real_glucose.csv", index=False)
    meal_df.to_csv(out_dir / "real_meals.csv", index=False)
    
    # Splits (stratified by hba1c tertile)
    prof_df['hba1c_filled'] = prof_df['hba1c'].fillna(prof_df['hba1c'].median())
    prof_df['tertile'] = pd.qcut(prof_df['hba1c_filled'], 3, labels=False)
    
    train_val_idx, test_idx = train_test_split(
        prof_df.index, 
        test_size=config['split']['test_ratio'],
        stratify=prof_df['tertile'],
        random_state=config['split']['random_seed']
    )
    
    val_ratio_adj = config['split']['val_ratio'] / (config['split']['train_ratio'] + config['split']['val_ratio'])
    train_idx, val_idx = train_test_split(
        train_val_idx,
        test_size=val_ratio_adj,
        stratify=prof_df.loc[train_val_idx, 'tertile'],
        random_state=config['split']['random_seed']
    )
    
    prof_df.loc[train_idx, 'split'] = 'train'
    prof_df.loc[val_idx, 'split'] = 'validation'
    prof_df.loc[test_idx, 'split'] = 'test'
    
    splits_df = prof_df[['patient_id', 'split']]
    splits_df.to_csv(out_dir / "real_splits.csv", index=False)
    
    total_days = gluc_df.groupby('recording_id')['timestamp'].apply(lambda x: (x.max() - x.min()).total_seconds() / 86400.0).sum()
    
    # Write quality report
    q_report = {
        "patients": len(prof_df),
        "recordings": len(prof_df),
        "total_days_recorded": float(total_days),
        "total_glucose_samples": int(total_glucose_samples),
        "impossible_glucose_dropped": int(impossible_glucose_total),
        "duplicate_timestamps_dropped": int(duplicate_timestamps_total),
        "gap_lengths_minutes": [float(g) for g in gap_lengths],
        "total_meals_recorded": len(meal_df),
        "missing_fields": missing_counts
    }
    with open("reports/real_data_quality.json", "w") as f:
        json.dump(q_report, f, indent=4)
        
    # Write seal report
    hasher = hashlib.sha256()
    with open(out_dir / "real_splits.csv", "rb") as f:
        hasher.update(f.read())
    with open("reports/real_data_seal.json", "w") as f:
        json.dump({"real_splits_sha256": hasher.hexdigest()}, f, indent=4)

if __name__ == "__main__":
    harmonize_shanghai_t2dm()
