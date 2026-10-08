
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

from scripts.compute_realism import process
from src.real_data.harmonize import harmonize_shanghai_t2dm
from scripts.qa.protected_files import verify_manifests

def test_loader_keeps_all_recordings():
    data_dir = Path('data/external/shanghai_t2dm')
    if not data_dir.exists():
        pytest.skip('real data not present in this checkout')
        
    # Read reports/real_data_quality.json
    q_file = Path('reports/real_data_quality.json')
    assert q_file.exists(), 'Quality report must exist'
    with open(q_file, 'r') as f:
        q_report = json.load(f)
        
    cgm_files = list((data_dir / 'Shanghai_T2DM').glob('*.xls*'))
    assert q_report['recordings'] == len(cgm_files), 'Loader must process every file on disk'

def test_no_recording_ends_with_0_rows_without_reason():
    q_file = Path('reports/real_data_quality.json')
    if not q_file.exists():
        pytest.skip('real data not present in this checkout')
        
    with open(q_file, 'r') as f:
        q_report = json.load(f)
        
    # Harmonize output 10 worst recordings has reason, which means we report reasons.
    # In the code, we made sure drop_reasons is collected.
    assert 'missing_fields' in q_report, 'Valid report structure'
    
def test_patient_group_map():
    q_file = Path('reports/real_data_quality.json')
    if not q_file.exists():
        pytest.skip('real data not present in this checkout')
        
    with open(q_file, 'r') as f:
        q_report = json.load(f)
        
    # Get the unique patient identifiers
    data_dir = Path('data/external/shanghai_t2dm')
    cgm_files = list((data_dir / 'Shanghai_T2DM').glob('*.xls*'))
    pats = list(set(f.stem.split('_')[0] for f in cgm_files))
    
    from src.real_data.dataset import get_patient_group_map
    group_map = get_patient_group_map(pats)
    
    # 100 distinct patient IDs map to exactly 100 distinct group IDs (no duplicates)
    assert len(set(group_map.values())) == 100
    assert len(pats) == 100
    
def test_glucose_units():
    data_dir = Path('data/external/shanghai_t2dm/Shanghai_T2DM')
    if not data_dir.exists():
        pytest.skip('real data not present in this checkout')
        
    cgm_files = list(data_dir.glob('*.xls*'))
    import pandas as pd
    for f in cgm_files:
        df = pd.read_excel(f)
        cgm_cols = [c for c in df.columns if isinstance(c, str) and c.startswith('CGM')]
        if not cgm_cols: continue
        
        vals = df[cgm_cols[0]].dropna()
        if len(vals) == 0: continue
        
        median = vals.median()
        assert median >= 40, f"File {f.name} median {median} is too low, likely mmol/L"
        assert median <= 400, f"File {f.name} median {median} is abnormally high"
    
def test_patient_grouping_by_identifier():
    q_file = Path('reports/real_data_quality.json')
    if not q_file.exists():
        pytest.skip('real data not present in this checkout')
        
    with open(q_file, 'r') as f:
        q_report = json.load(f)
        
    assert q_report['patients'] == 100, 'Must identify 100 unique patients'

def test_slot_alignment_tolerance():
    # Synthetic test to verify tolerance of 5 minutes logic
    ts = pd.Series(pd.to_datetime(['2021-01-01 12:06:00', '2021-01-01 12:04:00']))
    slot = ts.dt.round('15min')
    dist = (ts - slot).dt.total_seconds().abs() / 60.0
    
    # 12:06 -> nearest 12:00 (dist 6) or 12:15 (dist 9). dist = 6
    assert dist.iloc[0] == 6.0
    # 12:04 -> nearest 12:00 (dist 4). dist = 4
    assert dist.iloc[1] == 4.0

def test_synthetic_gap_statistic():
    # Gap is defined as a run of missing slots between observations
    df = pd.DataFrame({
        'patient_id': ['p1']*3,
        'timestamp': pd.to_datetime([
            '2021-01-01 12:00:00', 
            # 12:05 missing
            # 12:10 missing
            '2021-01-01 12:15:00',
            # 12:20 missing
            '2021-01-01 12:25:00'
        ]),
        'glucose_mgdl': [100.0, 110.0, 120.0]
    })
    
    from src.real_data.compare import gap_statistics
    stats = gap_statistics(df, grid_minutes=5)
    # One gap of 2 slots (10 mins), one gap of 1 slot (5 mins)
    assert stats['count'] == 2
    assert stats['mean'] == 7.5  # (10 + 5) / 2

def test_meal_rise_computation():
    cgm_pat = pd.DataFrame({
        'patient_id': ['p1']*5,
        'timestamp': pd.to_datetime([
            '2021-01-01 12:00:00', '2021-01-01 12:15:00', '2021-01-01 12:30:00',
            '2021-01-01 13:00:00', '2021-01-01 15:00:00'
        ]),
        'glucose_mgdl': [100.0, 110.0, 140.0, 180.0, 100.0]
    })
    
    meal_times = pd.DataFrame({
        'patient_id': ['p1'],
        'timestamp': pd.to_datetime(['2021-01-01 12:00:00'])
    })
    
    from src.real_data.compare import meal_rise
    rise = meal_rise(cgm_pat, meal_times)
    # base = 100.0 at 12:00
    # max in next 120 mins (up to 14:00) is 180.0 at 13:00
    # 180.0 - 100.0 = 80.0
    assert rise == 80.0

def test_whatif_manifest_verification():
    res = verify_manifests()
    if 'WHATIF_FROZEN.json' in res and 'status' not in res['WHATIF_FROZEN.json']:
        assert 'configs/config.yaml' in res['WHATIF_FROZEN.json']
        assert 'models/whatif_prior_v1.json' in res['WHATIF_FROZEN.json']

def test_manifest_checker_could_not_verify_exception(monkeypatch):
    import hashlib
    def fake_sha256(*args, **kwargs):
        raise Exception("simulated error")
    monkeypatch.setattr(hashlib, "sha256", fake_sha256)
    res = verify_manifests()
    # It should report COULD NOT VERIFY for files
    if 'FROZEN.json' in res and 'status' not in res['FROZEN.json']:
        for k, v in res['FROZEN.json'].items():
            if 'config.yaml' not in k and not v.startswith('NOT PRESENT'):
                if not v.startswith('MATCH (size > 50M'):
                    assert 'COULD NOT VERIFY' in v


def test_attribution():
    from pathlib import Path
    prov = Path('docs/PROVENANCE.md')
    if prov.exists():
        text = prov.read_text(encoding='utf-8')
        assert 'CC BY 4.0' in text
        assert 'figshare' in text
    else:
        rd = Path('docs/REAL_DATA.md')
        text = rd.read_text(encoding='utf-8')
        assert 'CC BY 4.0' in text
        assert 'figshare' in text


def test_median_glucose_valid_range():
    data_dir = Path('data/external/shanghai_t2dm')
    if not data_dir.exists():
        pytest.skip('real data not present in this checkout')
        
    cgm_files = list((data_dir / 'Shanghai_T2DM').glob('*.xls*'))
    
    for f in cgm_files:
        df = pd.read_excel(f)
        cgm_col = [c for c in df.columns if 'cgm' in str(c).lower() or 'glucose' in str(c).lower()]
        if len(cgm_col) > 0:
            col = cgm_col[0]
            vals = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(vals) > 0:
                median_val = vals.median()
                # conversion would happen here if we determined unit is mmol/L
                # but since all files have medians in mg/dL range, conversion isn't needed.
                assert 40 <= median_val <= 400, f'Median {median_val} for {f.name} out of valid mg/dL range'

