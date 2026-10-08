import pandas as pd
from pathlib import Path
import math

def check_units():
    data_dir = Path('data/external/shanghai_t2dm/Shanghai_T2DM')
    files = list(data_dir.glob('*.xls*'))
    
    out = []
    
    for f in files:
        df = pd.read_excel(f)
        cgm_cols = [c for c in df.columns if isinstance(c, str) and c.startswith('CGM')]
        if not cgm_cols:
            continue
        cgm_col = cgm_cols[0]
        
        vals = pd.to_numeric(df[cgm_col], errors='coerce').dropna()
        if len(vals) == 0: continue
        
        minimum = vals.min()
        median = vals.median()
        maximum = vals.max()
        
        # Check share of values that are multiples of 1.8
        # Since floats can have precision issues, we check if val % 1.8 is close to 0 or 1.8
        def is_multiple_of_1_8(v):
            rem = v % 1.8
            return rem < 1e-4 or (1.8 - rem) < 1e-4
            
        share = sum(is_multiple_of_1_8(v) for v in vals) / len(vals)
        
        conversion = "none (assumed mg/dL)"
        
        out.append({
            'file': f.name,
            'header': cgm_col,
            'min': minimum,
            'median': median,
            'max_before_conversion': maximum,
            'share_multiples_1_8': share,
            'conversion_applied': conversion
        })
        
    df_out = pd.DataFrame(out).sort_values('file')
    out_path = 'reports/real_units_per_file.csv'
    df_out.to_csv(out_path, index=False)
    
if __name__ == '__main__':
    check_units()
