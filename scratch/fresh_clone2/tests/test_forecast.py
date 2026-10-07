import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))

from src.forecast.consistency import estimate_spike_probability
from src.forecast.model import GlucoseForecaster
from src.forecast.targets import make_forecast_targets


def test_targets_logic():
    df = pd.DataFrame({
        "patient_id": [1, 1, 1, 1, 1],
        "timestamp": pd.date_range("2026-01-01 00:00", periods=5, freq="5min"),
        "glucose_mgdl": [100, 110, np.nan, 130, 140]
    })
    
    config = {
        "sampling_interval_minutes": 5,
        "forecast": {"horizons_minutes": [10]} # 2 steps
    }
    
    targets = make_forecast_targets(df, config)
    
    assert targets.loc[0, "target_valid_10m"] == 0
    assert targets.loc[1, "target_valid_10m"] == 1
    assert targets.loc[1, "target_delta_10m"] == 20
    assert targets.loc[3, "target_valid_10m"] == 0
    
def test_pchip_trajectory():
    config = {"forecast": {"horizons_minutes": [15, 30], "quantiles": [0.5]}, "sampling_interval_minutes": 5, "glucose_min": 40, "glucose_max": 400}
    model = GlucoseForecaster(config)
    curr = np.array([100])
    deltas = np.array([[[10], [20]]]) # 15m=+10, 30m=+20
    traj = model.get_trajectory(curr, deltas)
    
    # Steps: 0, 5, 10, 15, 20, 25, 30
    assert traj.shape == (1, 7, 1)
    assert traj[0, 0, 0] == 100
    assert traj[0, 3, 0] == 110
    assert traj[0, 6, 0] == 120
    
def test_spike_probability():
    deltas = np.array([[[10, 30, 50]]]) # q0=10, q1=30, q2=50
    p = estimate_spike_probability(deltas, threshold=50)
    assert np.isclose(p[0], 0.1)
    
    deltas = np.array([[[10, 50, 70]]])
    p = estimate_spike_probability(deltas, threshold=50)
    assert np.isclose(p[0], 0.5)
    
    deltas = np.array([[[50, 70, 90]]])
    p = estimate_spike_probability(deltas, threshold=50)
    assert np.isclose(p[0], 0.9)
