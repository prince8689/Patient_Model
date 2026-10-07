
import pandas as pd
import json
import subprocess
import os
import shutil
import sys

shutil.copy('src/twin/engine.py', 'scratch/engine_current.py')

def run_demo_and_get_logs(label):
    # Set PYTHONPATH
    env = os.environ.copy()
    env['PYTHONPATH'] = str(os.path.abspath('.'))
    subprocess.run([sys.executable, 'scripts/demonstrate_twin.py'], env=env, check=True)
    
    with open('reports/demo_demo_patient_3days.json', 'r') as f:
        log = json.load(f)
        
    df = pd.DataFrame([{
        'timestamp': s['timestamp'],
        'risk': s['risk_probability'],
        'band': s['risk_band'],
        'forecast_median': s.get('forecast_median', 0.0),
        'driver_sum': sum(s.get('risk_drivers', {}).values()) if s.get('risk_drivers') else 0.0
    } for s in log['steps']])
    
    return df

print('Running with current engine...')
df_current = run_demo_and_get_logs('current')

print('Restoring engine to HEAD (previous commit)...')
subprocess.run(['git', 'checkout', 'HEAD', '--', 'src/twin/engine.py'], check=True)

print('Running with HEAD engine...')
df_head = run_demo_and_get_logs('head')

print('Restoring engine to current...')
shutil.copy('scratch/engine_current.py', 'src/twin/engine.py')

max_risk_diff = (df_current['risk'] - df_head['risk']).abs().max()
max_forecast_diff = (df_current['forecast_median'] - df_head['forecast_median']).abs().max()
max_driver_diff = (df_current['driver_sum'] - df_head['driver_sum']).abs().max()
band_mismatches = (df_current['band'] != df_head['band']).sum()

print(f'\nMax absolute diffs:')
print(f'Risk probability: {max_risk_diff:.8e}')
print(f'Forecast median: {max_forecast_diff:.8e}')
print(f'Driver sum: {max_driver_diff:.8e}')
print(f'Band mismatches: {band_mismatches}')

