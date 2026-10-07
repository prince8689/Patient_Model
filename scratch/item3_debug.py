
import pandas as pd
import numpy as np
import scipy.stats

print('--- Real meals ---')
meals = pd.read_csv('data/processed/real_meals.csv')
print(meals.head())

print('--- Synthetic gaps ---')
orig_wearable = pd.read_csv('data/raw/wearable.csv')
orig_wearable['timestamp'] = pd.to_datetime(orig_wearable['timestamp'], format='mixed')
orig_wearable = orig_wearable.sort_values(['patient_id', 'timestamp'])
diffs = orig_wearable.groupby('patient_id')['timestamp'].diff().dt.total_seconds() / 60.0
gaps_5m = diffs[diffs > 5].dropna().tolist()
print(f'5m grid gaps count: {len(gaps_5m)}, median: {np.median(gaps_5m) if gaps_5m else 0}, mean: {np.mean(gaps_5m) if gaps_5m else 0}')

third_wearable = orig_wearable.iloc[::3].copy()
third_diffs = third_wearable.groupby('patient_id')['timestamp'].diff().dt.total_seconds() / 60.0
gaps_15m = third_diffs[third_diffs > 16].dropna().tolist()
print(f'15m grid gaps count: {len(gaps_15m)}, median: {np.median(gaps_15m) if gaps_15m else 0}, mean: {np.mean(gaps_15m) if gaps_15m else 0}')

print('--- Synthetic meal rise ---')
synth_meals = pd.read_csv('data/raw/meals.csv')
synth_meals['timestamp'] = pd.to_datetime(synth_meals['timestamp'], format='mixed')

rises = []
for _, m in synth_meals.head(100).iterrows():
    pid = m['patient_id']
    ts = m['timestamp']
    future = orig_wearable[(orig_wearable['patient_id'] == pid) & (orig_wearable['timestamp'] >= ts) & (orig_wearable['timestamp'] <= ts + pd.Timedelta(minutes=120))]
    if len(future) > 0:
        base = future.iloc[0]['glucose_mgdl']
        peak = future['glucose_mgdl'].max()
        rises.append(peak - base)
print(f'Sample synthetic rises: count={len(rises)}, mean={np.mean(rises)}')


