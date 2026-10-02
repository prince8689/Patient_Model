import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.twin.loader import TwinRegistry
from src.twin.replay import StreamReplayer
from src.utils.config import load_config


def main():
    config = load_config()
    fig_dir = Path(config["paths"]["reports"]) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    registry = TwinRegistry(config)
    splits = pd.read_csv(Path(config["paths"]["data_processed"]) / "splits.csv")
    test_pats = splits[splits["split"] == config["twin"]["demo_patient_split"]]["patient_id"].unique()
    pat = test_pats[0]
    
    twin = registry.get(pat)
    replayer = StreamReplayer(Path(config["paths"]["data_raw"]) / "wearable.csv", pat)
    stream = list(replayer.stream())
    
    states = []
    warmup = int(config["twin"]["warmup_hours"] * 60 / config["sampling_interval_minutes"])
    for i, s in enumerate(stream[:warmup + 100]):
        st = twin.ingest(s)
        if i >= warmup:
            states.append(st)
            
    st = states[-1]
    
    plt.figure(figsize=(10, 5))
    df_hist = pd.DataFrame(twin.buffer)
    plt.plot(df_hist["timestamp"], df_hist["glucose_mgdl"], 'k.-', alpha=0.5, label="History")
    
    curr = st.latest_measurement.glucose_mgdl
    ts = pd.to_datetime(st.timestamp)
    plt.plot([ts], [curr], 'ko', markersize=8)
    
    if st.forecast:
        f = st.forecast
        xs = pd.to_datetime(f.trajectory_5min["timestamp"])
        y_med = f.trajectory_5min["median"]
        y_low = f.trajectory_5min["lower"]
        y_high = f.trajectory_5min["upper"]
        
        plt.plot(xs, y_med, 'b*-', label="Forecast (Median)")
        plt.fill_between(xs, y_low, y_high, color='b', alpha=0.2, label="80% CI")
        
        plt.axvspan(ts, ts + pd.Timedelta(minutes=120), color='gray', alpha=0.1)
        
        plt.axhline(config["forecast"]["hyper_threshold_mgdl"], color='r', linestyle='--', alpha=0.5, label="Hyper Threshold")
        plt.axhline(config["forecast"]["hypo_threshold_mgdl"], color='r', linestyle=':', alpha=0.5, label="Hypo Threshold")
            
    plt.title(f"Live Twin Forecast for Patient {pat}\n{st.forecast.summary if st.forecast else ''}")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "demo_live_forecast.png", dpi=150)
    plt.close()
    
    print("Demo figure saved.")

if __name__ == "__main__":
    main()
