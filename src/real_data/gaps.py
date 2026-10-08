import pandas as pd
import numpy as np

def compute_slots_and_gaps(timestamps, slot_interval_minutes=15):
    """
    Computes total slots and gap statistics for a single recording's timestamps.
    Returns:
        total_slots (int): ((last - first) / interval) + 1
        missing_slots (int): total_slots - len(timestamps)
        gaps (list of int): lengths of each gap in minutes
    """
    if len(timestamps) == 0:
        return 0, 0, []
        
    ts = pd.Series(timestamps).sort_values().reset_index(drop=True)
    first_ts = ts.iloc[0]
    last_ts = ts.iloc[-1]
    
    interval = pd.Timedelta(minutes=slot_interval_minutes)
    
    # Calculate total slots
    total_slots = int((last_ts - first_ts) / interval) + 1
    missing_slots = total_slots - len(ts)
    
    # Calculate gaps
    # A gap is a run of missing slots between observed timestamps.
    # The number of missing slots between two consecutive observed timestamps t1, t2 is:
    # missing_slots = ((t2 - t1) / interval) - 1
    # If missing_slots > 0, it's a gap. The length of the gap is missing_slots * interval
    diffs = ts.diff().dropna()
    slots_between = (diffs / interval).round().astype(int)
    gap_slots = slots_between - 1
    gaps = gap_slots[gap_slots > 0].values * slot_interval_minutes
    
    return total_slots, missing_slots, list(gaps)

def compute_gap_stats_for_dataset(df_glucose, slot_interval_minutes=15):
    """
    Computes aggregated gap stats for the entire dataset containing multiple recordings.
    df_glucose must have 'recording_id' and 'timestamp' columns.
    """
    all_gaps = []
    total_slots_all = 0
    missing_slots_all = 0
    
    for rec_id, group in df_glucose.groupby('recording_id'):
        ts = group['timestamp']
        slots, missing, gaps = compute_slots_and_gaps(ts, slot_interval_minutes)
        total_slots_all += slots
        missing_slots_all += missing
        all_gaps.extend(gaps)
        
    all_gaps = np.array(all_gaps)
    count = len(all_gaps)
    median = float(np.median(all_gaps)) if count > 0 else 0.0
    mean = float(np.mean(all_gaps)) if count > 0 else 0.0
    
    return {
        "total_slots": int(total_slots_all),
        "missing_slots": int(missing_slots_all),
        "gap_count": int(count),
        "gap_median": float(median),
        "gap_mean": float(mean),
        "gaps_per_1000_slots": float(count / total_slots_all * 1000) if total_slots_all > 0 else 0.0,
        "gaps_per_patient_day": float(count / (total_slots_all * slot_interval_minutes / 1440.0)) if total_slots_all > 0 else 0.0,
        "share_missing_slots": float(missing_slots_all / total_slots_all) if total_slots_all > 0 else 0.0
    }
