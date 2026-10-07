
import pandas as pd
from pathlib import Path
f = Path('data/external/shanghai_t2dm/Shanghai_T2DM/2000_0_20201230.xlsx')
df = pd.read_excel(f)
row = df.iloc[0]
for k, v in row.items():
    if isinstance(k, str): k = k.encode('ascii', 'ignore').decode()
    if isinstance(v, str): v = v.encode('ascii', 'ignore').decode()
    print(f'{k}: {v}')

