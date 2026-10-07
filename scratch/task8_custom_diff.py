
import pandas as pd
import numpy as np
import json
import subprocess
import os
import sys
import shutil

shutil.copy('src/twin/engine.py', 'scratch/engine_current.py')

def run_custom_demo():
    script = '''
import sys
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
sys.path.append(os.path.abspath('.'))

from src.utils.config import load_config
from src.twin.loader import TwinRegistry
from src.twin.replay import StreamReplayer

config = load_config()
registry = TwinRegistry(config)
df_wear = pd.read_csv('data/raw/wearable.csv')
pat1 = df_wear['patient_id'].unique()[0]

twin = registry.get(pat1)
replayer = StreamReplayer('data/raw/wearable.csv', pat1)

stream = list(replayer.stream())[:int(3*24*60/5)]
results = []
for s in stream:
    st = twin.ingest(s)
    if st.risk:
        driver_sum = sum([d['shap_value'] for d in st.risk.drivers]) if st.risk.drivers else 0.0
        
        forecast_val = 0.0
        if st.forecast:
            forecast_val = st.forecast.predicted_peak
            
        results.append({
            'timestamp': st.timestamp,
            'risk': st.risk.probability_calibrated,
            'band': st.risk.band,
            'forecast': forecast_val,
            'drivers': driver_sum
        })

with open('scratch/demo_output.json', 'w') as f:
    json.dump(results, f)
'''
    with open('scratch/temp_demo.py', 'w') as f:
        f.write(script)
    
    env = os.environ.copy()
    subprocess.run([sys.executable, 'scratch/temp_demo.py'], env=env, check=True)
    with open('scratch/demo_output.json', 'r') as f:
        return pd.DataFrame(json.load(f))

print('Running current engine...')
df_current = run_custom_demo()

print('Restoring HEAD engine...')
subprocess.run(['git', 'checkout', 'HEAD', '--', 'src/twin/engine.py'], check=True)

print('Running HEAD engine...')
df_head = run_custom_demo()

print('Restoring current engine...')
shutil.copy('scratch/engine_current.py', 'src/twin/engine.py')

max_risk_diff = (df_current['risk'] - df_head['risk']).abs().max()
max_forecast_diff = (df_current['forecast'] - df_head['forecast']).abs().max()
max_driver_diff = (df_current['drivers'] - df_head['drivers']).abs().max()
band_mismatches = (df_current['band'] != df_head['band']).sum()

print('--- Engine Diff ---')
print(f'Max Risk Diff: {max_risk_diff:.8e}')
print(f'Max Forecast Diff: {max_forecast_diff:.8e}')
print(f'Max Driver Sum Diff: {max_driver_diff:.8e}')
print(f'Band Mismatches: {band_mismatches}')

