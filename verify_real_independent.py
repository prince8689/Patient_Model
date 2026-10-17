"""Independent check of the ShanghaiT2DM numbers.

This script does not import anything from the project. It reads the raw Excel
files directly and recomputes: reading counts, glucose range, how many readings
fall outside several candidate valid ranges, glucose level statistics, and the
label prevalence (glucose rise of at least 50 mg/dL within the next 120
minutes) for each candidate range.

Usage (PowerShell, from the project folder):
    .\\.venv\\Scripts\\python verify_real_independent.py data\\external\\shanghai_t2dm
Needs pandas, numpy, openpyxl and xlrd (the project environment has them).
"""
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

HORIZON_MIN = 120
RISE_MG_DL = 50.0
STEP_MIN = 15
COVERAGE = 0.8


def find_t2dm_folder(root):
    for dirpath, dirnames, _ in os.walk(root):
        if "__MACOSX" in dirpath:
            continue
        if os.path.basename(dirpath) == "Shanghai_T2DM":
            return dirpath
    raise SystemExit(f"No folder named Shanghai_T2DM found under {root}")


def read_recording(path):
    df = pd.read_excel(path)
    cols = list(df.columns)
    time_col = next((c for c in cols if str(c).strip().lower().startswith("date")), cols[0])
    cgm_col = next((c for c in cols if str(c).strip().lower().startswith("cgm")), None)
    if cgm_col is None:
        raise ValueError(f"no CGM column in {os.path.basename(path)}; columns: {cols}")
    out = pd.DataFrame({
        "t": pd.to_datetime(df[time_col], errors="coerce"),
        "g": pd.to_numeric(df[cgm_col], errors="coerce"),
    }).dropna()
    out = out.drop_duplicates("t").sort_values("t").reset_index(drop=True)
    return out, str(cgm_col)


def label_recording(t_min, g):
    """Return (valid_count, positive_count) using time-based windows."""
    n = len(g)
    valid = pos = 0
    need = int(np.ceil(COVERAGE * HORIZON_MIN / STEP_MIN))
    end_time = t_min[-1]
    for i in range(n):
        t0 = t_min[i]
        if end_time < t0 + HORIZON_MIN - STEP_MIN / 2:
            break  # window not inside the recording
        right = np.searchsorted(t_min, t0 + HORIZON_MIN + 1e-9, side="right")
        window = g[i + 1:right]
        if len(window) < need:
            continue
        valid += 1
        if window.max() >= g[i] + RISE_MG_DL:
            pos += 1
    return valid, pos


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "external", "shanghai_t2dm")
    folder = find_t2dm_folder(root)
    files = sorted(f for f in os.listdir(folder)
                   if f.lower().endswith((".xls", ".xlsx")) and not f.startswith("."))
    print(f"folder: {folder}")
    print(f"recording files: {len(files)}")

    recs, headers = {}, Counter()
    for f in files:
        data, header = read_recording(os.path.join(folder, f))
        recs[f] = data
        headers[header] += 1
    patients = {f.split("_")[0] for f in recs}
    print(f"patients (from file names): {len(patients)}")
    print("CGM column headers:", dict(headers))

    allg = np.concatenate([d["g"].to_numpy() for d in recs.values()])
    print(f"\nreadings with a time stamp and a glucose value: {len(allg)}")
    print(f"minimum {allg.min():.1f}  median {np.median(allg):.1f}  maximum {allg.max():.1f}")
    print(f"below 40: {(allg < 40).sum()}   above 400: {(allg > 400).sum()}   above 500: {(allg > 500).sum()}")
    vc = Counter(np.round(allg[(allg < 40) | (allg > 400)], 1))
    print("most common values outside 40 to 400:", vc.most_common(10))
    mult = np.isclose(allg / 1.8, np.round(allg / 1.8), atol=1e-6).mean()
    print(f"share of values that are multiples of 1.8: {mult:.4f}")

    print("\nCandidate valid ranges (readings outside the range are removed before labels):")
    rows = []
    for lo, hi in [(0, 10_000), (40, 400), (40, 500), (39, 501)]:
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
        pm = np.mean([np.concatenate(v).mean() for v in per_patient.values()])
        rows.append({
            "range": f"{lo} to {hi}", "readings": len(kg),
            "mean_pooled": round(kg.mean(), 2), "mean_per_patient": round(pm, 2),
            "below_70": round((kg < 70).mean(), 4),
            "70_to_180": round(((kg >= 70) & (kg <= 180)).mean(), 4),
            "above_180": round((kg > 180).mean(), 4),
            "label_rows": valid, "positives": pos,
            "prevalence": round(pos / valid, 4) if valid else float("nan"),
        })
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nLabel here: maximum glucose in the next 120 minutes at least 50 mg/dL above the current "
          "value; window must lie inside the recording and hold at least 7 of the 8 expected readings; "
          "windows use time stamps, not grid slots.")
    print("Numbers reported by the project (for comparison): 112,462 raw readings; mean 141.1; "
          "above 180 0.196; below 70 0.023; prevalence 0.1386 (earlier 0.1194 appeared once).")


if __name__ == "__main__":
    main()
