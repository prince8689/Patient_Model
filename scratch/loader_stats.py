import pandas as pd
rg = pd.read_csv('data/processed/real_glucose.csv')

# old dropping logic dropped if the timestamp minute was not in [0, 15, 30, 45]
# Let's find which patients are they
import glob
from pathlib import Path
data_dir = Path('data/external/shanghai_t2dm/Shanghai_T2DM')
files = list(data_dir.glob('*.xls*'))
all_kept = []
new_pats = []
for f in files:
    df = pd.read_excel(f)
    cgm_col = [c for c in df.columns if 'cgm' in str(c).lower() or 'glucose' in str(c).lower()][0]
    time_col = [c for c in df.columns if 'time' in str(c).lower() or 'date' in str(c).lower()][0]
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    obs = df.dropna(subset=[cgm_col, time_col])
    
    # how many were kept in rg?
    rec_id = f.stem
    rg_obs = rg[rg['recording_id'] == rec_id].dropna(subset=['glucose_mgdl'])
    
    kept_share = len(rg_obs) / len(obs) if len(obs) > 0 else 0
    all_kept.append({'recording': rec_id, 'kept_share': kept_share, 'raw_rows': len(obs), 'kept_rows': len(rg_obs)})

    # old logic:
    if len(obs) > 0:
        minutes = obs[time_col].dt.minute
        if not minutes.isin([0, 15, 30, 45]).all():
            new_pats.append({'recording': rec_id, 'kept_rows': len(rg_obs)})
            
ak_df = pd.DataFrame(all_kept)
print('Summary of kept share:')
print(ak_df['kept_share'].describe())
print('\n10 worst kept share:')
print(ak_df.sort_values('kept_share').head(10))

print('\nDropped by old loader (new row counts):')
for np in new_pats:
    print(f"{np['recording']}: {np['kept_rows']} rows")
