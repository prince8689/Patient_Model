import json
import pandas as pd
import numpy as np
from src.twin.loader import TwinRegistry
from src.utils.config import load_config
from src.app_lib.data_access import get_patient_wearable

config = load_config()
registry = TwinRegistry(config)

demo_patients = ['P007', 'P008', 'P028', 'P031', 'P038', 'P040']
timestamps = {
    'P007': '2026-01-03 21:50:00',
    'P028': '2026-01-07 21:40:00',
    'P031': '2026-01-09 22:15:00',
    'P040': '2026-01-03 22:20:00',
    'P008': '2026-01-02 14:50:00',
    'P038': '2026-01-03 22:35:00'
}

max_diff = 0.0
diff_fields = set()

for pid in demo_patients:
    ts_str = timestamps[pid]
    as_of = pd.to_datetime(ts_str)
    
    # Load bundled state
    fpath = f'demo_bundle/states/{pid}_{as_of.strftime("%Y%m%d_%H%M")}.json'
    with open(fpath) as f:
        bundled = json.load(f)
        
    # Stream through normal ingest
    twin = registry.get(pid)
    wearable = get_patient_wearable(pid)
    wearable = wearable[wearable['timestamp'] <= as_of]
    samples = wearable.to_dict(orient='records')
    
    for s in samples[:-1]:
        twin.ingest(s)
    state = twin.ingest(samples[-1])
    engine_state = state.to_dict()
    
    # Compare
    # Risk probability
    if bundled.get('risk') and engine_state.get('risk'):
        p_bund = bundled['risk'].get('probability_calibrated', 0)
        p_eng = engine_state['risk'].get('probability_calibrated', 0)
        diff = abs(p_bund - p_eng)
        max_diff = max(max_diff, diff)
        if diff > 1e-6: diff_fields.add('risk.probability_calibrated')
        
        if bundled['risk'].get('band') != engine_state['risk'].get('band'):
            diff_fields.add('risk.band')
            
        b_drivers = [d['feature'] for d in bundled['risk'].get('drivers', [])[:3]]
        e_drivers = [d['feature'] for d in engine_state['risk'].get('drivers', [])[:3]]
        if b_drivers != e_drivers:
            diff_fields.add('risk.drivers')
            
    if bundled.get('forecast') and bundled['forecast'].get('status') == 'ok' and engine_state.get('forecast'):
        b_traj = bundled['forecast']['trajectory_5min']['median']
        e_traj = engine_state['forecast']['trajectory_5min']['median']
        for v1, v2 in zip(b_traj, e_traj):
            diff = abs(v1 - v2)
            max_diff = max(max_diff, diff)
            if diff > 1e-6: diff_fields.add('forecast.median')

if not diff_fields:
    print('No differences found.')
else:
    print('Differing fields:', diff_fields)
print(f'Max absolute diff: {max_diff}')
