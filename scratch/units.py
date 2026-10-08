import pandas as pd
from pathlib import Path
res = []
for f in Path('data/external/shanghai_t2dm/Shanghai_T2DM').glob('*.xls*'):
    df = pd.read_excel(f, nrows=0)
    c = [col for col in df.columns if 'cgm' in str(col).lower() or 'glucose' in str(col).lower()]
    res.append({'file': f.name, 'col': c[0] if c else None})
print(pd.DataFrame(res)['col'].value_counts())
