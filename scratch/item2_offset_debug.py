
import pandas as pd
from pathlib import Path

f = list(Path('data/external/shanghai_t2dm/Shanghai_T2DM').glob('2000_0_20201230.xls*'))[0]
ts_df = pd.read_excel(f)
cgm_col = [c for c in ts_df.columns if isinstance(c, str) and c.startswith('CGM')][0]
cgm = ts_df[['Date', cgm_col]].dropna().copy()
cgm = cgm.rename(columns={'Date': 'timestamp', cgm_col: 'glucose_mgdl'})
cgm['initial_slot'] = cgm['timestamp'].dt.round('15min')
cgm['initial_offset'] = (cgm['timestamp'] - cgm['initial_slot']).dt.total_seconds() / 60.0
print('Before:')
print(cgm[['timestamp', 'initial_slot', 'initial_offset']].head())

median_offset = cgm['initial_offset'].median()
print(f'Median offset: {median_offset}')
if abs(median_offset) > 5.0:
    cgm['timestamp'] = cgm['timestamp'] - pd.Timedelta(minutes=median_offset)

cgm['slot'] = cgm['timestamp'].dt.round('15min')
cgm['dist'] = (cgm['timestamp'] - cgm['slot']).dt.total_seconds().abs() / 60.0
print('After:')
print(cgm[['timestamp', 'slot', 'dist']].head())

