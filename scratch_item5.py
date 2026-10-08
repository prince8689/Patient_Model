import pandas as pd
from pathlib import Path
import json

def get_recordings():
    data_dir = Path('data/external/shanghai_t2dm/Shanghai_T2DM')
    cgm_files = list(data_dir.glob('*.xls*'))
    
    # Load actual parsed data
    gluc_df = pd.read_csv('data/processed/real_glucose.csv')
    counts = gluc_df.groupby('recording_id').size().to_dict()
    
    out = []
    for f in cgm_files:
        stem = f.stem
        pat_id = stem.split('_')[0]
        
        out.append({
            'source_file_name': f.name,
            'recording_id': stem,
            'patient_id': pat_id,
            'rows_loaded': counts.get(stem, 0)
        })
        
    df = pd.DataFrame(out).sort_values('recording_id')
    print(df.to_markdown(index=False))
    
if __name__ == '__main__':
    get_recordings()
