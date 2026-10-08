import pandas as pd
from pathlib import Path

files = list(Path('data/external/shanghai_t2dm/Shanghai_T2DM').glob('*.xls*'))
below = 0
above = 0

for f in files:
    df = pd.read_excel(f)
    cgm_cols = [c for c in df.columns if isinstance(c, str) and c.startswith('CGM')]
    if len(cgm_cols) > 0:
        v = df[cgm_cols[0]].dropna()
        below += sum(v < 40)
        above += sum(v > 400)

print(f'Below 40: {below}')
print(f'Above 400: {above}')
