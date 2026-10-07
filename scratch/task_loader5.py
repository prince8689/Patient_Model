
import pandas as pd
import numpy as np
from pathlib import Path

f = Path('data/external/shanghai_t2dm/Shanghai_T2DM/2000_0_20201230.xlsx')
ts_df = pd.read_excel(f)
cgm = ts_df[['Date', 'CGM (mg / dl)']].dropna().copy()
cgm = cgm.rename(columns={'Date': 'timestamp', 'CGM (mg / dl)': 'glucose_mgdl'})
cgm['slot'] = cgm['timestamp'].dt.round('15min')
cgm['offset'] = (cgm['timestamp'] - cgm['slot']).dt.total_seconds() / 60.0
print(cgm['offset'].median())

