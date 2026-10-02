import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config


def get_events(df_pat):
    """Returns list of events (start_idx, end_idx) where spike_next_2h == 1, merging gaps < 6 (30m)."""
    df_pat = df_pat.reset_index(drop=True)
    spike_idx = df_pat[df_pat["spike_next_2h"] == 1].index.values
    if len(spike_idx) == 0:
        return []
        
    events = []
    curr_start = spike_idx[0]
    curr_end = spike_idx[0]
    
    for idx in spike_idx[1:]:
        if idx - curr_end <= 6: # 30 mins
            curr_end = idx
        else:
            events.append((curr_start, curr_end))
            curr_start = idx
            curr_end = idx
    events.append((curr_start, curr_end))
    return events

def analyze_utility(df_test, t_alert, cooldown_steps=12):
    n_days = len(df_test) * 5 / (60 * 24)
    alerts = 0
    caught = 0
    total_events = 0
    lead_times = []
    
    for pid, grp in df_test.groupby("patient_id"):
        grp = grp.sort_values("timestamp").reset_index(drop=True)
        events = get_events(grp)
        total_events += len(events)
        
        # Simulate alerts
        last_alert_idx = -999
        alert_indices = []
        for i, row in grp.iterrows():
            if row["prob_calib"] >= t_alert:
                if i - last_alert_idx >= cooldown_steps:
                    alert_indices.append(i)
                    last_alert_idx = i
                    
        alerts += len(alert_indices)
        
        # Check caught events
        alert_set = set(alert_indices)
        for start, end in events:
            # Look for alert in [start - 24, start] (up to 120m before onset)
            window = range(max(0, start - 24), start + 1)
            valid_alerts = alert_set.intersection(window)
            if valid_alerts:
                caught += 1
                first_alert = min(valid_alerts)
                lead_times.append((start - first_alert) * 5)
                
    alerts_per_day = alerts / n_days if n_days > 0 else 0
    recall = caught / total_events if total_events > 0 else 0
    precision = caught / alerts if alerts > 0 else 0
    med_lead = np.median(lead_times) if lead_times else 0
    
    return alerts_per_day, recall, precision, med_lead, lead_times

def main():
    config = load_config()
    reports_path = Path(config["paths"]["reports"])
    fig_dir = reports_path / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    df_test = pd.read_parquet(reports_path / "test_predictions_day7.parquet")
    
    with open(Path(config["paths"]["models"]) / "thresholds_v1.json", "r") as f:
        thresholds = json.load(f)
    t_med = thresholds["thresholds"]["t_medium"]
    t_high = thresholds["thresholds"]["t_high"]
    
    # 1. Alert burden and recall
    print("Evaluating Medium Threshold...")
    med_apd, med_rec, med_prec, med_lt, med_lts = analyze_utility(df_test, t_med)
    print("Evaluating High Threshold...")
    high_apd, high_rec, high_prec, high_lt, high_lts = analyze_utility(df_test, t_high)
    
    # 2. Rule baseline vs XGBoost sweep
    print("Sweeping thresholds for curve...")
    ts = np.linspace(0.01, 0.99, 50)
    xgb_curve = []
    for t in ts:
        apd, rec, _, _, _ = analyze_utility(df_test, t)
        xgb_curve.append((apd, rec))
        
    # Hack rule probabilities to get a point
    df_test["prob_calib_backup"] = df_test["prob_calib"]
    df_test["prob_calib"] = df_test["prob_rule"]
    rule_apd, rule_rec, _, _, _ = analyze_utility(df_test, 0.5)
    df_test["prob_calib"] = df_test["prob_calib_backup"]
    
    print(f"XGBoost @ t_med: {med_apd:.2f} alerts/day, {med_rec:.2%} recall, {med_lt:.0f}m median lead time")
    print(f"Rule-based: {rule_apd:.2f} alerts/day, {rule_rec:.2%} recall")
    
    # Save plots
    plt.figure(figsize=(8, 6))
    x_val = [c[0] for c in xgb_curve]
    y_val = [c[1] for c in xgb_curve]
    plt.plot(x_val, y_val, label="XGBoost")
    plt.scatter([rule_apd], [rule_rec], color='red', label="Rule-based")
    plt.scatter([med_apd], [med_rec], color='orange', label=f"t_med ({t_med:.2f})")
    plt.scatter([high_apd], [high_rec], color='green', label=f"t_high ({t_high:.2f})")
    plt.xlabel("Alerts per Patient per Day")
    plt.ylabel("Event-level Recall")
    plt.title("Clinical Utility: Recall vs Alert Burden")
    plt.legend()
    plt.grid(True)
    plt.savefig(fig_dir / "day7_event_recall_vs_alert_burden.png", dpi=150)
    plt.close()
    
    plt.figure(figsize=(8, 5))
    bins = config["evaluation"]["lead_time_bins_minutes"]
    plt.hist(med_lts, bins=bins, color="skyblue", edgecolor="black")
    plt.title(f"Lead Time Histogram (t_med)\nMedian: {med_lt:.0f} mins")
    plt.xlabel("Lead Time (Minutes)")
    plt.ylabel("Events Caught")
    plt.savefig(fig_dir / "day7_lead_time_hist.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    main()
