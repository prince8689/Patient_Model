
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
