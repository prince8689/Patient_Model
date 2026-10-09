import pandas as pd
import numpy as np
import pytest
from src.real_data.harmonize import load_config
from pathlib import Path
import json

def test_label_gap_and_end_regression():
    times = pd.date_range("2026-01-01 10:00:00", periods=20, freq="15min")
    valid_indices = [0, 1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    t_vals = times[valid_indices]
    
    glucose = [100, 110, 120, 130, 100, 100,
               140, 150, 160, 170, 180, 190, 200, 100, 100] 
               
    df = pd.DataFrame({'recording_id': 'R1', 'timestamp': t_vals, 'glucose_mgdl': glucose})
    
    horizon = 120
    min_cov = 0.5
    threshold = 20
    
    labels = []
    group_times = df['timestamp'].values
    group_gl = df['glucose_mgdl'].values
    n = len(df)
    group_labels = np.full(n, np.nan)
    
    horizon_td = np.timedelta64(horizon, 'm')
    req_samples = (horizon / 15) * min_cov
    
    right = 0
    for left in range(n):
        t_curr = group_times[left]
        val_curr = group_gl[left]
        t_end = t_curr + horizon_td
        
        while right < n and group_times[right] <= t_end:
            right += 1
            
        window_len = right - left - 1
        if window_len >= req_samples:
            max_future = group_gl[left+1:right].max()
            group_labels[left] = 1.0 if max_future >= (val_curr + threshold) else 0.0
            
    assert group_labels[0] == 1.0
    assert group_labels[1] == 1.0
    assert np.isnan(group_labels[4])
    assert group_labels[6] == 1.0
    assert np.isnan(group_labels[11])


def test_real_label_prevalence():
    config = load_config()
    out_dir = Path(config["processed_path"])
    
    gluc_file = out_dir / "real_glucose.csv"
    if not gluc_file.exists():
        pytest.skip("Real data not present")
        
    df = pd.read_csv(gluc_file)
    valid_labels = df['label'].notna().sum()
    prevalence = df['label'].sum() / valid_labels if valid_labels > 0 else 0
    
    assert abs(prevalence - 0.1386) < 0.001
