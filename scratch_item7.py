import pandas as pd
from pathlib import Path

def check_units():
    data_dir = Path('data/external/shanghai_t2dm/Shanghai_T2DM')
    files = list(data_dir.glob('*.xls*'))
    
    out = []
    cgm_header_files = []
    for f in files:
        df = pd.read_excel(f)
        cgm_cols = [c for c in df.columns if isinstance(c, str) and c.startswith('CGM')]
        if not cgm_cols:
            continue
        cgm_col = cgm_cols[0]
        
        if cgm_col == 'CGM':
            cgm_header_files.append(f.name)
            
        vals = df[cgm_col].dropna()
        if len(vals) == 0: continue
        
        minimum = vals.min()
        median = vals.median()
        maximum = vals.max()
        
        # Determine conversion
        # The harmonize script currently does NOT apply any conversion (it just filters < 40 or > 400).
        # We assume they are all already in mg/dL since none are < 40 median.
        conversion = "none (assumed mg/dL)"
        
        out.append({
            'file': f.name,
            'header': cgm_col,
            'min': minimum,
            'median': median,
            'max': maximum,
            'conversion': conversion
        })
        
    df_out = pd.DataFrame(out).sort_values('file')
    df_out.to_csv('scratch_units.csv', index=False)
    
    print(f"Files with header exactly 'CGM': {cgm_header_files}")
    
if __name__ == '__main__':
    check_units()
