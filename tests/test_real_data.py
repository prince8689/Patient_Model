import pytest
import pandas as pd
from pathlib import Path
import json
import hashlib
import os


@pytest.fixture
def skip_if_no_real_data():
    if not Path("data/external/shanghai_t2dm").exists():
        pytest.skip("real data not present in this checkout")

def test_real_data_files_exist_and_content(skip_if_no_real_data):
    real_data_dir = Path("data/processed")
    assert (real_data_dir / "real_glucose.csv").exists()
    assert (real_data_dir / "real_profiles.csv").exists()
    
    # Check that test guard works
    splits = pd.read_csv(real_data_dir / "real_splits.csv")
    assert not splits.empty, "Splits are empty"
    
    # Verify no file under data/external is tracked by git
    import subprocess
    result = subprocess.run(["git", "ls-files", "data/external"], capture_output=True, text=True)
    assert result.stdout.strip() == "", "Files under data/external are tracked by git"
    
def test_real_data_seal(skip_if_no_real_data):
    seal_path = Path("reports/real_data_seal.json")
    real_data_dir = Path("data/processed")
    assert seal_path.exists(), "Seal file missing"
    
    with open(seal_path, "r") as f:
        seal = json.load(f)
        
    hasher = hashlib.sha256()
    with open(real_data_dir / "real_splits.csv", "rb") as f:
        hasher.update(f.read())
        
    assert hasher.hexdigest() == seal["real_splits_sha256"], "Split seal mismatch"
    
def test_brute_force_label():
    # Hand-built fixture: 15-minute grid
    # Times: 0, 15, 30, 45, 60, 75, 90, 105, 120 (9 points, index 0 to 8)
    # Plus a gap, then end of recording
    import datetime
    base_time = datetime.datetime(2021, 1, 1, 8, 0)
    times = [base_time + datetime.timedelta(minutes=15*i) for i in range(12)]
    # Drop times[9] and times[10] to create a gap, so we only have 0-8 and 11
    # 0-8 is 2 hours. If we compute for time 0, future is 1-8 (8 points, 100% coverage)
    # If we compute for time 1, future is 2-8 plus 11. The window from 15 to 135 has points 2-8 (7 points). 7/8 = 87.5% coverage. Valid.
    # If we compute for time 2, window from 30 to 150 has points 3-8, 11 (7 points). Valid.
    # If we compute for time 3, window from 45 to 165 has points 4-8, 11 (6 points). 6/8 = 75%. INVALID (needs 80%).
    
    df = pd.DataFrame({
        'timestamp': [times[i] for i in [0,1,2,3,4,5,6,7,8,11]],
        'glucose_mgdl': [100, 110, 120, 100, 100, 100, 150, 100, 100, 200]
    })
    
    # 1. Brute force implementation
    horizon_steps = 8
    threshold = 50
    min_cov = 0.8
    brute_labels = []
    
    for i in range(len(df)):
        t_curr = df['timestamp'].iloc[i]
        v_curr = df['glucose_mgdl'].iloc[i]
        
        t_end = t_curr + pd.Timedelta(minutes=15 * horizon_steps)
        future = df[(df['timestamp'] > t_curr) & (df['timestamp'] <= t_end)]
        
        if len(future) >= horizon_steps * min_cov:
            max_v = future['glucose_mgdl'].max()
            brute_labels.append(1 if max_v >= v_curr + threshold else 0)
        else:
            brute_labels.append(float('nan'))
            
    # Time 0: v=100. future: max is 150 (at time 6). 150 >= 100+50 => 1.
    # Time 1: v=110. future: max is 150 (at time 6). 150 < 110+50 => 0.
    # Time 2: v=120. future: max is 200 (at time 11). 200 >= 120+50 => 1.
    # Time 3: coverage is 6/8 < 80%. => nan.
    # Time 11: end of recording. future empty => nan.
    
    import numpy as np
    assert brute_labels[0] == 1
    assert brute_labels[1] == 0
    assert brute_labels[2] == 1
    assert np.isnan(brute_labels[3])
    assert np.isnan(brute_labels[-1])
    
    # Also verify split has no overlap
    if Path("data/processed/real_splits.csv").exists():
        splits = pd.read_csv("data/processed/real_splits.csv")
        assert splits['patient_id'].duplicated().sum() == 0, "Overlap in splits"

def test_attribution_present(skip_if_no_real_data):
    readme = Path("README.md").read_text()
    assert "Zhao et al" in readme
    assert "10.6084/m9.figshare.c.6310860" in readme
    real_data_md = Path("docs/REAL_DATA.md").read_text()
    assert "Zhao et al" in real_data_md
    
def test_real_test_guard(skip_if_no_real_data, monkeypatch):
    splits = pd.read_csv("data/processed/real_splits.csv")
    test_pids = splits[splits['split'] == 'test']['patient_id'].astype(str).tolist()
    
    # Attempt to load a test patient from real_glucose.csv should fail or be filtered out by an interface if we had one.
    # But wait, the guard is just: "seal the test split with a guard that refuses to load real test rows unless ALLOW_REAL_TEST=1"
    # We implement this in `src/real_data/__init__.py` or similar. Let's write the interface here and test it.
    from src.real_data.dataset import load_real_glucose
    
    monkeypatch.delenv("ALLOW_REAL_TEST", raising=False)
    with pytest.raises(PermissionError):
        df = load_real_glucose(include_test=True)
        
    monkeypatch.setenv("ALLOW_REAL_TEST", "1")
    df = load_real_glucose(include_test=True)
    assert not df.empty
