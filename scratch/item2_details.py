import pandas as pd
import numpy as np
import os
import json
import yaml
from pathlib import Path
from collections import Counter

def load_config() -> dict:
    with open('configs/real_data.yaml', 'r') as f:
        return yaml.safe_load(f)

def run():
    config = load_config()
    raw_dir = Path(config['data_path'])
    
    # a. File counts
    counts = Counter()
    for path in raw_dir.rglob('*'):
        if path.is_file():
            ext = path.suffix.lower()
            counts[f'{path.parent.name}/{ext}'] += 1
            
    print('--- a. File counts ---')
    for k, v in sorted(counts.items()):
        print(f'{k}: {v}')
        
    summary_file = raw_dir / 'Shanghai_T2DM_Summary.xlsx'
    data_folder = raw_dir / 'Shanghai_T2DM'
    summary_df = pd.read_excel(summary_file, sheet_name='T2DM')
    
    prof_pids = set()
    for _, row in summary_df.iterrows():
        rec_id = str(row['Patient Number'])
        pid = rec_id.split('_')[0]
        prof_pids.add(pid)
        
    cgm_files = list(data_folder.glob('*.xls*'))
    print(f'CGM files opened: {len(cgm_files)}')
    
    cgm_pids = set()
    rec_to_pid = {}
    pid_to_recs = Counter()
    
    skipped = []
    
    for f in cgm_files:
        rec_id = f.stem
        pid = rec_id.split('_')[0]
        cgm_pids.add(pid)
        rec_to_pid[rec_id] = pid
        pid_to_recs[pid] += 1
        
        try:
            ts_df = pd.read_excel(f)
        except Exception as e:
            skipped.append(f'{rec_id}: {e}')
            continue
            
        if 'Date' not in ts_df.columns:
            skipped.append(f'{rec_id}: Missing Date column')
            continue
            
        cgm_col = [c for c in ts_df.columns if isinstance(c, str) and c.startswith('CGM')]
        if not cgm_col:
            skipped.append(f'{rec_id}: Missing CGM column')
            continue
            
        cgm_col_name = cgm_col[0]
        
        cgm = ts_df[['Date', cgm_col_name]].copy()
        raw_len = len(cgm)
        
        if rec_id in ['2000_0_20201230', '2002_0_20210513', '2014_0_20201224']:
            print(f'\n--- b. Debug {rec_id} ---')
            print(f'Raw rows: {raw_len}')
            print(f'Nulls in Date: {cgm["Date"].isna().sum()}')
            print(f'Nulls in CGM: {cgm[cgm_col_name].isna().sum()}')
            cgm_valid = cgm.dropna()
            print(f'Rows after dropna: {len(cgm_valid)}')
            if len(cgm_valid) > 0:
                print(f'Date head:\n{cgm_valid["Date"].head(3)}')
                print(f'CGM head:\n{cgm_valid[cgm_col_name].head(3)}')
            print('--------------------------')
            
    print('\n--- d. Patient Identifiers ---')
    print(f'Unique in CGM files: {len(cgm_pids)}')
    print(f'Unique in Profiles: {len(prof_pids)}')
    overlap = cgm_pids.intersection(prof_pids)
    print(f'Overlap: {len(overlap)}')
    print(f'Patients without CGM: {prof_pids - cgm_pids}')
    
    recs_without_prof = [r for r, p in rec_to_pid.items() if p not in prof_pids]
    print(f'Recordings without profile: {recs_without_prof}')
    
    multi_recs = {p: c for p, c in pid_to_recs.items() if c > 1}
    print(f'Patients with >1 recording count: {len(multi_recs)}')
    
    print(f'\n--- Skips ---')
    for s in skipped:
        print(s)

run()
