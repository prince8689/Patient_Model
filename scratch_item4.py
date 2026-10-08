import json
from pathlib import Path
import pandas as pd

def check():
    q_file = Path('reports/real_data_quality.json')
    with open(q_file, 'r') as f:
        q_report = json.load(f)
        
    data_dir = Path('data/external/shanghai_t2dm')
    cgm_files = list((data_dir / 'Shanghai_T2DM').glob('*.xls*'))
    
    loaded_pats = set()
    for f in cgm_files:
        stem = f.stem
        pat_id = stem.split('_')[0]
        loaded_pats.add(pat_id)
        
    dups = ['2065', '2068', '2071', '2072']
    found = [d for d in dups if d in loaded_pats]
    print(f"Loaded patients: {len(loaded_pats)}")
    print(f"Duplicates found in loaded: {found}")
    
    # Let's see what the loader outputs natively
    from src.real_data.dataset import load_shanghai_t2dm
    df = load_shanghai_t2dm()
    print("N unique in df:", df['patient_id'].nunique())
    print("Duplicates in df:", [d for d in dups if d in df['patient_id'].unique()])

if __name__ == "__main__":
    check()
