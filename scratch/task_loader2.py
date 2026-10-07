
import pandas as pd
from pathlib import Path
for rec_id in ['2000_0_20201230', '2002_0_20210513', '2014_0_20201224']:
    f = Path(f'data/external/shanghai_t2dm/Shanghai_T2DM/{rec_id}.xlsx')
    if not f.exists():
        f = Path(f'data/external/shanghai_t2dm/Shanghai_T2DM/{rec_id}.xls')
    df = pd.read_excel(f)
    print(f'\n--- {rec_id} ---')
    cols = df.columns.tolist()
    print('Columns:', [c.encode('ascii', 'ignore').decode() for c in cols if isinstance(c, str)])
    cgm_col = [c for c in cols if isinstance(c, str) and 'CGM' in c]
    date_col = [c for c in cols if isinstance(c, str) and 'Date' in c]
    if cgm_col and date_col:
        print(df[[date_col[0], cgm_col[0]]].head())

