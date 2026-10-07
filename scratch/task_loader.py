
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import datetime

config = {'data_path': 'data/external/shanghai_t2dm', 'processed_path': 'data/processed'}
raw_dir = Path(config['data_path'])
data_folder = raw_dir / 'Shanghai_T2DM'
summary_file = raw_dir / 'Shanghai_T2DM_Summary.xlsx'

summary_df = pd.read_excel(summary_file, sheet_name='T2DM')
profiles = set()
for _, row in summary_df.iterrows():
    rec_id = str(row['Patient Number'])
    pid = rec_id.split('_')[0]
    profiles.add(pid)

cgm_files = list(data_folder.glob('*.xls*'))
cgm_pids = set()
cgm_recs = set()

opened = 0
skipped = []
recording_stats = []

for f in cgm_files:
    rec_id = f.stem
    pid = rec_id.split('_')[0]
    cgm_pids.add(pid)
    cgm_recs.add(rec_id)
    opened += 1
    
    try:
        ts_df = pd.read_excel(f)
    except Exception as e:
        skipped.append((rec_id, str(e)))
        continue
        
    ts_df = ts_df.sort_values('Date').reset_index(drop=True)
    
    if 'CGM (mg / dl)' not in ts_df.columns or 'Date' not in ts_df.columns:
        skipped.append((rec_id, 'Missing required columns'))
        continue
        
    cgm = ts_df[['Date', 'CGM (mg / dl)']].dropna().copy()
    cgm = cgm.rename(columns={'Date': 'timestamp', 'CGM (mg / dl)': 'glucose_mgdl'})
    
    raw_len = len(cgm)
    
    if raw_len == 0:
        skipped.append((rec_id, '0 rows after dropna'))
        recording_stats.append({
            'recording_id': rec_id,
            'raw': raw_len,
            'final': 0,
            'kept_ratio': 0,
            'drop_reason': 'dropna'
        })
        continue
        
    # Investigating why specific recordings lose all rows
    cgm['slot'] = cgm['timestamp'].dt.round('15min')
    cgm['dist'] = (cgm['timestamp'] - cgm['slot']).dt.total_seconds().abs() / 60.0
    
    too_far = (cgm['dist'] > 5.0)
    cgm = cgm[~too_far].copy()
    too_far_len = too_far.sum()
    
    # Deduplicate slots
    cgm = cgm.sort_values(by=['slot', 'dist'])
    dup_slots = cgm.duplicated(subset=['slot'], keep='first')
    cgm = cgm[~dup_slots].copy()
    dup_slots_len = dup_slots.sum()
    
    final_len = len(cgm)
    recording_stats.append({
        'recording_id': rec_id,
        'raw': raw_len,
        'final': final_len,
        'kept_ratio': final_len / raw_len if raw_len > 0 else 0,
        'drop_reason': f'too_far={too_far_len}, dup={dup_slots_len}'
    })

print(f'CGM files opened: {opened}')
print(f'Skipped files: {skipped}')
overlap = profiles.intersection(cgm_pids)
print(f'Profiles unique PIDs: {len(profiles)}')
print(f'CGM unique PIDs: {len(cgm_pids)}')
print(f'Overlap PIDs: {len(overlap)}')

