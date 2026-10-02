import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.twin.loader import TwinRegistry
from src.twin.replay import StreamReplayer
from src.twin.timeline import build_timeline
from src.utils.config import load_config


def main():
    config = load_config()
    fig_dir = Path(config["paths"]["reports"]) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    splits = pd.read_csv(Path(config["paths"]["data_processed"]) / "splits.csv")
    test_pats = splits[splits["split"] == "test"]["patient_id"].unique()
    pat1 = test_pats[0]
    
    print(f"Generating Fast Timeline for {pat1}...")
    df_tl = build_timeline(pat1, config=config)
    
    # 1. Timeline Example
    print("Plotting Timeline Example...")
    # Get 2 days of data
    start_idx = len(df_tl) // 2
    df_plot = df_tl.iloc[start_idx:start_idx+int(48*60/5)].copy()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    ax1.plot(df_plot["timestamp"], df_plot["glu_current"], color="blue", label="Glucose")
    ax1.set_ylabel("Glucose (mg/dL)")
    ax1.set_title(f"Twin Timeline - Patient {pat1}")
    ax1.axhline(180, color='r', linestyle='--', alpha=0.5)
    ax1.axhline(70, color='r', linestyle='--', alpha=0.5)
    
    ax2.plot(df_plot["timestamp"], df_plot["probability"], color="purple", label="Risk")
    ax2.set_ylabel("Probability")
    
    # Shade bands
    with open(Path(config["paths"]["models"]) / "thresholds_v1.json", "r") as f:
        th = json.load(f)["thresholds"]
        
    ax2.axhspan(0, th["t_medium"], color="green", alpha=0.1, label="Low Risk")
    ax2.axhspan(th["t_medium"], th["t_high"], color="yellow", alpha=0.2, label="Medium Risk")
    ax2.axhspan(th["t_high"], 1.0, color="red", alpha=0.1, label="High Risk")
    
    alerts = df_plot[df_plot["alert_fired"] == True]
    if not alerts.empty:
        ax2.scatter(alerts["timestamp"], alerts["probability"], color="red", marker="*", s=100, zorder=5, label="Alert Fired")
        
    ax2.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(fig_dir / "twin_timeline_example.png", dpi=150)
    plt.close()
    
    # 2. State Snapshot
    print("Generating State Snapshot...")
    from src.twin.timeline import get_state_at
    # Pick a timestamp where an alert fired
    if not alerts.empty:
        snap_ts = alerts.iloc[0]["timestamp"].isoformat()
    else:
        snap_ts = df_plot.iloc[-1]["timestamp"].isoformat()
        
    state = get_state_at(pat1, snap_ts, config)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis("off")
    text = "TwinState Snapshot\n====================\n"
    text += f"Patient: {state.profile.patient_id} | Age: {state.profile.age} | HbA1c: {state.profile.hba1c}\n"
    text += f"Timestamp: {state.timestamp}\n"
    text += f"Glucose: {state.glucose_summary.current_glucose} mg/dL (Trend: {state.glucose_summary.trend_direction})\n"
    text += f"Context: {state.context.minutes_since_last_meal}m since meal, {state.context.carbs_on_board_estimate:.1f}g COB\n"
    text += f"Risk: {state.risk.probability_calibrated:.1%} ({state.risk.band} Band)\n\n"
    text += "Top Drivers:\n"
    if state.risk.drivers:
        for i, d in enumerate(state.risk.drivers):
            text += f"  {i+1}. {d['human_readable']} (SHAP: {d['shap_value']:.2f})\n"
    text += f"\nData Quality: {state.data_quality.status} (Conf: {state.data_quality.confidence})\n"
    if state.active_alert:
        text += f"\n*** ALERT: {state.active_alert.message} ***\n"
        
    ax.text(0.05, 0.95, text, va='top', family='monospace', size=10)
    plt.savefig(fig_dir / "twin_state_snapshot.png", dpi=150)
    plt.close()
    
    # 3. Fault recovery
    print("Running Fault Recovery Demo...")
    registry = TwinRegistry(config)
    twin = registry.get(test_pats[1])
    
    df_wear = pd.read_csv(Path(config["paths"]["data_raw"]) / "wearable.csv")
    df_wear = df_wear[df_wear["patient_id"] == test_pats[1]]
    start_ts = df_wear["timestamp"].iloc[0]
    # stream 36 hours for warmup
    replayer = StreamReplayer(Path(config["paths"]["data_raw"]) / "wearable.csv", test_pats[1])
    stream = list(replayer.stream())[:int(36*60/5) + 50]
    
    # Inject a 2-hour gap at the end
    gap_stream = stream[:-24] + stream[-1:] # Drop 24 samples before the last one
    
    xs, ys, probs, statuses = [], [], [], []
    for s in gap_stream[-50:]:
        st = twin.ingest(s)
        xs.append(pd.to_datetime(st.timestamp))
        ys.append(st.latest_measurement.glucose_mgdl)
        probs.append(st.risk.probability_calibrated if st.risk else np.nan)
        statuses.append(st.data_quality.status)
        
    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(xs, ys, 'o-', color='blue')
    ax1.set_title("2-Hour Gap Fault Recovery")
    ax1.set_ylabel("Glucose", color='blue')
    ax2 = ax1.twinx()
    ax2.plot(xs, probs, 'x--', color='purple')
    ax2.set_ylabel("Risk Prob", color='purple')
    
    # annotate status
    last_status = None
    for x, y, s in zip(xs, ys, statuses):
        if s != last_status:
            ax1.annotate(s, (x, 150), rotation=90, color="red")
            last_status = s
            
    plt.tight_layout()
    plt.savefig(fig_dir / "fault_recovery.png", dpi=150)
    plt.close()
    
    # 4. Latency
    print("Running Latency Benchmark...")
    twin_lat = registry.get(test_pats[2])
    latencies = []
    latencies_drivers = []
    
    for s in stream[:int(24*60/5)]:
        t0 = time.time()
        st = twin_lat.ingest(s)
        t1 = time.time()
        ms = (t1 - t0) * 1000
        latencies.append(ms)
        if st.risk and st.risk.drivers:
            latencies_drivers.append(ms)
            
    plt.figure(figsize=(8, 4))
    plt.hist(latencies, bins=30, alpha=0.7, label="All Samples")
    if latencies_drivers:
        plt.hist(latencies_drivers, bins=30, alpha=0.7, label="With Drivers")
    plt.title("Ingest Latency per Sample (ms)")
    plt.xlabel("Latency (ms)")
    plt.legend()
    plt.savefig(fig_dir / "latency.png", dpi=150)
    plt.close()
    
    med_all = np.median(latencies)
    p95_all = np.percentile(latencies, 95)
    print(f"Latency All: Median={med_all:.1f}ms, P95={p95_all:.1f}ms")
    if latencies_drivers:
        print(f"Latency Drivers: Median={np.median(latencies_drivers):.1f}ms")
        
    print("Done generating Day 8 figures.")

if __name__ == "__main__":
    main()
