import pandas as pd
import numpy as np
import os
import json
import hashlib
import yaml
from pathlib import Path

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
    
    profiles = {}
    
    missing_counts = {
        "age": 0, "sex": 0, "bmi": 0, "hba1c": 0, "diabetes_duration": 0,
        "use_insulin": 0, "use_metformin": 0, "hypertension": 0
    }
    
    # Load all profiles
    for _, row in summary_df.iterrows():
        rec_id = str(row['Patient Number'])
        pid = rec_id.split('_')[0]
        if pid not in profiles:
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
            
            profiles[pid] = {
                "patient_id": pid,
                "age": age,
                "sex": sex,
                "bmi": bmi,
                "hba1c": hba1c,
                "diabetes_duration": duration,
                "use_insulin": use_insulin,
                "use_metformin": use_metformin,
                "hypertension": hypertension
            }
            
    cgm_files = list(data_folder.glob("*.xls*"))
    
    glucose_records = []
    meal_records = []
    
    gap_lengths = []
    duplicate_timestamps_total = 0
    impossible_glucose_total = 0
    total_raw_rows = 0
    total_glucose_samples = 0
    total_moved = 0
    total_dropped_too_far = 0
    total_dropped_slot_dup = 0
    
    recording_stats = []
    skipped_files = []
    
    for f in cgm_files:
        rec_id = f.stem
        pid = rec_id.split('_')[0]
        
        print(f"Reading {f.name}...")
        try:
            ts_df = pd.read_excel(f)
        except Exception as e:
            skipped_files.append((rec_id, str(e)))
            continue
            
        if 'Date' not in ts_df.columns:
            skipped_files.append((rec_id, "Missing Date column"))
            continue
            
        cgm_col = [c for c in ts_df.columns if isinstance(c, str) and c.startswith('CGM')]
        if not cgm_col:
            skipped_files.append((rec_id, "Missing CGM column"))
            continue
            
        cgm_col_name = cgm_col[0]
            
        ts_df = ts_df.sort_values('Date').reset_index(drop=True)
        
        # Glucose
        cgm = ts_df[['Date', cgm_col_name]].dropna().copy()
        cgm = cgm.rename(columns={'Date': 'timestamp', cgm_col_name: 'glucose_mgdl'})
        
        raw_len = len(cgm)
        total_raw_rows += raw_len
        
        if raw_len == 0:
            skipped_files.append((rec_id, "0 rows after dropna"))
            recording_stats.append({
                'recording_id': rec_id,
                'raw': raw_len,
                'final': 0,
                'kept_ratio': 0,
                'drop_reasons': "dropna"
            })
            continue
            
        drop_reasons = []
        
        dups = cgm.duplicated(subset=['timestamp'])
        dup_count = dups.sum()
        if dup_count > 0:
            drop_reasons.append(f"dup_ts:{dup_count}")
        duplicate_timestamps_total += dup_count
        cgm = cgm[~dups]
        
        impossible = ((cgm['glucose_mgdl'] < 40) | (cgm['glucose_mgdl'] > 400))
        imp_count = impossible.sum()
        if imp_count > 0:
            drop_reasons.append(f"impossible_glu:{imp_count}")
        impossible_glucose_total += imp_count
        cgm = cgm[~impossible]
        
        if len(cgm) == 0:
            recording_stats.append({
                'recording_id': rec_id,
                'raw': raw_len,
                'final': 0,
                'kept_ratio': 0,
                'drop_reasons': ", ".join(drop_reasons)
            })
            continue
            
        # Compute grid alignment using circular median of minute-of-day mod 15
        mod_15 = (cgm['timestamp'].dt.hour * 60 + cgm['timestamp'].dt.minute + cgm['timestamp'].dt.second / 60.0) % 15
        mod_15_arr = mod_15.to_numpy()[:, None]
        phases = np.linspace(0, 15, 150)
        dists = np.minimum((mod_15_arr - phases) % 15, (phases - mod_15_arr) % 15)
        phase = phases[np.argmin(dists.sum(axis=0))]
        
        phase_td = pd.Timedelta(minutes=phase)
        cgm['slot'] = (cgm['timestamp'] - phase_td).dt.round('15min') + phase_td
        cgm['dist'] = (cgm['timestamp'] - cgm['slot']).dt.total_seconds().abs() / 60.0
        
        moved = (cgm['dist'] > 0).sum()
        total_moved += moved
        
        too_far = cgm['dist'] > 5.0
        too_far_count = too_far.sum()
        
        # If >2% of readings outside tolerance, flag and print residual distribution
        if too_far_count > 0.02 * len(cgm):
            print(f"Warning: {rec_id} has {too_far_count}/{len(cgm)} readings outside 5min tolerance. Phase: {phase:.2f}. Residual dist: {cgm['dist'].describe().to_dict()}")
            
        if too_far_count > 0:
            drop_reasons.append(f"dist_too_far:{too_far_count}")
        total_dropped_too_far += too_far_count
        cgm = cgm[~too_far].copy()
        
        # Deduplicate slots (keep closest)
        cgm = cgm.sort_values(by=['slot', 'dist'])
        dup_slots = cgm.duplicated(subset=['slot'], keep='first')
        dup_slot_count = dup_slots.sum()
        if dup_slot_count > 0:
            drop_reasons.append(f"dup_slot:{dup_slot_count}")
        total_dropped_slot_dup += dup_slot_count
        cgm = cgm[~dup_slots].copy()
        
        cgm['timestamp'] = cgm['slot']  # Snap to grid
        cgm = cgm.drop(columns=['slot', 'dist'])
        cgm = cgm.sort_values('timestamp').reset_index(drop=True)
        
        final_len = len(cgm)
        total_glucose_samples += final_len
        
        recording_stats.append({
            'recording_id': rec_id,
            'raw': raw_len,
            'final': final_len,
            'kept_ratio': final_len / raw_len if raw_len > 0 else 0,
            'phase': float(phase),
            'moved': int(moved),
            'collisions': int(dup_slot_count),
            'drop_reasons': ", ".join(drop_reasons) if drop_reasons else "none"
        })
        
        # Print only if drops exist or for testing, but instruction says "Store offset, number moved, collisions and dropped rows with reasons per recording."
        
        if len(cgm) > 1:
            diffs = cgm['timestamp'].diff().dt.total_seconds() / 60.0
            gaps = diffs[diffs > 16].dropna().tolist()
            gap_lengths.extend(gaps)
            
        cgm['patient_id'] = pid
        cgm['recording_id'] = rec_id
        glucose_records.append(cgm)
        
        # Meals
        if 'Dietary intake' in ts_df.columns:
            meals = ts_df[['Date', 'Dietary intake']].dropna().copy()
            for _, m_row in meals.iterrows():
                meal_records.append({
                    "patient_id": pid,
                    "recording_id": rec_id,
                    "timestamp": m_row['Date'],
                    "dietary_intake_text": str(m_row['Dietary intake']),
                    "carbs_g": np.nan
                })

    prof_df = pd.DataFrame(list(profiles.values()))
    gluc_df = pd.concat(glucose_records, ignore_index=True)
    meal_df = pd.DataFrame(meal_records)
    
    # Compute labels correctly on snapped data
    horizon = config['labeling']['horizon_minutes']
    threshold = config['labeling']['threshold_mgdl']
    min_cov = config['labeling']['min_coverage_ratio']
    
    labels = []
    # Since data is exactly 15 min spaced, we just check rolling windows per recording
    for rec_id, group in gluc_df.groupby('recording_id'):
        group = group.sort_values('timestamp')
        
        for i in range(len(group)):
            t_curr = group['timestamp'].iloc[i]
            val_curr = group['glucose_mgdl'].iloc[i]
            
            t_end = t_curr + pd.Timedelta(minutes=horizon)
            future = group[(group['timestamp'] > t_curr) & (group['timestamp'] <= t_end)]
            
            if len(future) >= (horizon / 15) * min_cov:
                max_future = future['glucose_mgdl'].max()
                label = 1 if max_future >= (val_curr + threshold) else 0
                labels.append(label)
            else:
                labels.append(np.nan)
                
    gluc_df['label'] = labels
    
    valid_labels = gluc_df['label'].notna().sum()
    prevalence = gluc_df['label'].mean()
    
    # Save CSVs
    prof_df.to_csv(out_dir / "real_profiles.csv", index=False)
    gluc_df.to_csv(out_dir / "real_glucose.csv", index=False)
    meal_df.to_csv(out_dir / "real_meals.csv", index=False)
    
    total_days = gluc_df.groupby('recording_id')['timestamp'].apply(lambda x: (x.max() - x.min()).total_seconds() / 86400.0).sum() if len(gluc_df) > 0 else 0
    
    gap_lengths = np.array(gap_lengths)
    gap_stats = {
        "count": int(len(gap_lengths)),
        "median": float(np.median(gap_lengths)) if len(gap_lengths) > 0 else 0.0,
        "mean": float(np.mean(gap_lengths)) if len(gap_lengths) > 0 else 0.0
    }
    
    # Write quality report
    q_report = {
        "patients": len(prof_df),
        "recordings": len(recording_stats),
        "total_days_recorded": float(total_days),
        "days_per_recording": float(total_days / len(recording_stats)) if len(recording_stats) > 0 else 0.0,
        "raw_cgm_rows": int(total_raw_rows),
        "duplicate_timestamps_dropped": int(duplicate_timestamps_total),
        "impossible_glucose_dropped": int(impossible_glucose_total),
        "rows_moved_to_grid": int(total_moved),
        "dropped_too_far_from_grid": int(total_dropped_too_far),
        "dropped_duplicate_in_slot": int(total_dropped_slot_dup),
        "total_glucose_samples_final": int(total_glucose_samples),
        "total_slots_per_grid": int(total_days * 96),
        "missing_slots": int((total_days * 96) - total_glucose_samples),
        "missing_share": 1.0 - (total_glucose_samples / (total_days * 96)) if total_days > 0 else 0.0,
        "valid_labels": int(valid_labels),
        "label_prevalence": float(prevalence) if valid_labels > 0 else 0.0,
        "gap_length_distribution": gap_stats,
        "total_meals_recorded": len(meal_df),
        "missing_fields": missing_counts
    }
    with open("reports/real_data_quality.json", "w") as f:
        json.dump(q_report, f, indent=4)
        
    print(f"Skipped files: {skipped_files}")
    print(f"Raw rows: {total_raw_rows}")
    print(f"Final rows: {total_glucose_samples}")
    print(f"Valid label rows: {valid_labels} (Prevalence: {prevalence:.4f})")
    
    # Print 10 worst recordings by kept_ratio
    stats_df = pd.DataFrame(recording_stats).sort_values('kept_ratio')
    print("\nOverall share kept summary:")
    print(stats_df['kept_ratio'].describe())
    print("\n10 worst recordings:")
    print(stats_df.head(10).to_string(index=False))

if __name__ == "__main__":
    harmonize_shanghai_t2dm()
