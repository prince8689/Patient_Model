import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

# Add repo root to path to import verify_real_independent
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from verify_real_independent import find_t2dm_folder, read_recording, label_recording


def compute_real_range_stats(data_root=None):
    if data_root is None:
        data_root = root / "data" / "external" / "shanghai_t2dm"
    folder = find_t2dm_folder(str(data_root))
    files = sorted(f for f in os.listdir(folder)
                   if f.lower().endswith((".xls", ".xlsx")) and not f.startswith("."))

    recs = {}
    for f in files:
        data, _ = read_recording(os.path.join(folder, f))
        recs[f] = data

    allg = np.concatenate([d["g"].to_numpy() for d in recs.values()])
    total_readings = int(len(allg))
    floor_value = 39.6
    floor_readings = int((allg == floor_value).sum())
    above_400_readings = int((allg > 400).sum())
    maximum_glucose = float(round(allg.max(), 1))

    # Candidate valid ranges
    candidate_ranges = [(0, 10_000), (40, 400), (40, 500), (39, 501)]
    prevalence_by_range = {}
    range_details = {}

    for lo, hi in candidate_ranges:
        kept_g, valid, pos = [], 0, 0
        per_patient = {}
        for f, d in recs.items():
            m = (d["g"] >= lo) & (d["g"] <= hi)
            dd = d[m].reset_index(drop=True)
            if len(dd) == 0:
                continue
            t_min = (dd["t"] - dd["t"].iloc[0]).dt.total_seconds().to_numpy() / 60.0
            gg = dd["g"].to_numpy()
            v, p = label_recording(t_min, gg)
            valid += v
            pos += p
            kept_g.append(gg)
            per_patient.setdefault(f.split("_")[0], []).append(gg)

        kg = np.concatenate(kept_g)
        patient_means = [np.concatenate(v).mean() for v in per_patient.values()]
        patient_below_70 = [(np.concatenate(v) < 70).mean() for v in per_patient.values()]
        patient_above_180 = [(np.concatenate(v) > 180).mean() for v in per_patient.values()]

        prev = round(pos / valid, 4) if valid else float("nan")
        range_str = f"{lo} to {hi}"
        prevalence_by_range[range_str] = prev
        range_details[range_str] = {
            "readings": int(len(kg)),
            "mean_pooled": float(round(kg.mean(), 2)),
            "mean_per_patient": float(round(np.mean(patient_means), 2)),
            "time_below_70_pooled": float(round((kg < 70).mean(), 4)),
            "time_below_70_per_patient": float(round(np.mean(patient_below_70), 4)),
            "time_above_180_pooled": float(round((kg > 180).mean(), 4)),
            "time_above_180_per_patient": float(round(np.mean(patient_above_180), 4)),
            "label_rows": int(valid),
            "positives": int(pos),
            "prevalence": prev,
        }

    # Time below 70 with and without floor readings
    # "with floor readings" corresponds to candidate range 0 to 10000 (or 39 to 501)
    # "without floor readings" corresponds to 40 to 500 (or 40 to 400)
    time_below_70_with_floor = {
        "pooled": range_details["0 to 10000"]["time_below_70_pooled"],
        "per_patient": range_details["0 to 10000"]["time_below_70_per_patient"]
    }
    time_below_70_without_floor = {
        "pooled": range_details["40 to 500"]["time_below_70_pooled"],
        "per_patient": range_details["40 to 500"]["time_below_70_per_patient"]
    }

    patient_level_mean_glucose = {
        "with_floor": range_details["0 to 10000"]["mean_per_patient"],
        "without_floor": range_details["40 to 500"]["mean_per_patient"]
    }

    report = {
        "total_readings": total_readings,
        "valid_range_low": 40,
        "valid_range_high": 500,
        "floor_value_mgdl": floor_value,
        "floor_value_mmol": 2.2,
        "readings_at_floor": floor_readings,
        "readings_above_400": above_400_readings,
        "maximum_glucose": maximum_glucose,
        "prevalence_by_range": prevalence_by_range,
        "time_below_70_with_floor": time_below_70_with_floor,
        "time_below_70_without_floor": time_below_70_without_floor,
        "patient_level_mean_glucose": patient_level_mean_glucose,
        "candidate_range_details": range_details
    }

    out_path = root / "reports" / "real_range_check.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    rep = compute_real_range_stats()
    print(json.dumps(rep, indent=2))
