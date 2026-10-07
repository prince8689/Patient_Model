import pandas as pd
import glob
from pathlib import Path

data_dir = Path('data/external/shanghai_t2dm/Shanghai_T2DM')
files = list(data_dir.glob('*.xls*'))
results = []
for f in files:
    try:
        df = pd.read_excel(f)
        cgm_col = [c for c in df.columns if 'cgm' in str(c).lower() or 'glucose' in str(c).lower()]
        if len(cgm_col) > 0:
            col = cgm_col[0]
            vals = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(vals) > 0:
                results.append({
                    'file': f.name,
                    'header': str(col),
                    'min': vals.min(),
                    'median': vals.median(),
                    'max': vals.max()
                })
    except Exception as e:
        print(f'Error reading {f.name}: {e}')

df_res = pd.DataFrame(results)
print("Files with header not 'CGM (mg / dl)':")
for _, r in df_res[df_res['header'] != 'CGM (mg / dl)'].iterrows():
    print(f"{r['file']}: '{r['header']}' (min: {r['min']}, median: {r['median']}, max: {r['max']})")

df_res.to_csv('scratch/units_check.csv', index=False)
