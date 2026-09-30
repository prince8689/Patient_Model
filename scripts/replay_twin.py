import sys
import argparse
from pathlib import Path
import json
import time

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.twin.loader import TwinRegistry
from src.twin.replay import StreamReplayer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patient", required=True)
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--realtime", action="store_true")
    parser.add_argument("--fault", choices=["none", "duplicate", "out_of_order", "gap", "corrupted"], default="none")
    args = parser.parse_args()
    
    config = load_config()
    registry = TwinRegistry(config)
    twin = registry.get(args.patient)
    
    # Get test split start time
    df_splits = pd.read_csv(Path(config["paths"]["data_processed"]) / "splits.csv")
    test_start = "2026-01-01" # simplify
    
    # Stream
    replayer = StreamReplayer(Path(config["paths"]["data_raw"]) / "wearable.csv", args.patient)
    stream = list(replayer.stream())
    
    n_samples = args.days * 24 * 12
    stream = stream[:n_samples]
    
    if args.fault == "duplicate":
        if len(stream) > 100:
            stream.insert(100, stream[100])
    elif args.fault == "out_of_order":
        if len(stream) > 100:
            tmp = stream[100]
            stream[100] = stream[101]
            stream[101] = tmp
    elif args.fault == "gap":
        if len(stream) > 150:
            # Drop 2 hours (24 samples) at index 100
            stream = stream[:100] + stream[124:]
    elif args.fault == "corrupted":
        if len(stream) > 100:
            stream[100]["glucose_mgdl"] = -5
            
    print(f"Replaying {len(stream)} samples for {args.patient}...")
    
    latencies = []
    
    for i, sample in enumerate(stream):
        t0 = time.time()
        state = twin.ingest(sample)
        t1 = time.time()
        latencies.append((t1 - t0) * 1000)
        
        # Live log
        ts = state.timestamp
        g = state.glucose_summary.current_glucose
        band = state.risk.band if state.risk else "N/A"
        prob = state.risk.probability_calibrated if state.risk else 0.0
        
        driver = ""
        if state.risk and state.risk.drivers:
            driver = state.risk.drivers[0]["human_readable"]
            
        alert = f" [ALERT: {state.active_alert.message}]" if state.active_alert else ""
        warns = f" [WARN: {','.join(state.data_quality.warnings)}]" if state.data_quality.warnings else ""
        
        print(f"[{ts}] Glu: {g:>5} | Risk: {prob:>5.1%} ({band:<6}) | {driver}{alert}{warns}")
        
        if args.realtime:
            time.sleep(0.1)

    import numpy as np
    print(f"\nLatency: Median = {np.median(latencies):.1f} ms, P95 = {np.percentile(latencies, 95):.1f} ms")
    
    # Save demo output
    out = state.to_dict()
    out_dir = Path("reports") / "twin_states"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / f"demo_state_{args.patient}.json", "w") as f:
        json.dump(out, f, indent=2)
        
if __name__ == "__main__":
    import pandas as pd
    main()
