import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(root))
    out = res.stdout.strip()
    if res.stderr.strip():
        if out:
            out += "\n"
        out += res.stderr.strip()
    return out

lines = []
lines.append("=== Item 2: Realism Comparison Generation & Validation ===")

# 1. Execute committed script src.real_data.compare
lines.append("\n--- 1. Execution of src.real_data.compare ---")
compare_output = run_cmd(".\\.venv\\Scripts\\python -m src.real_data.compare")
lines.append(compare_output)

# 2. Inspect generated reports/realism_comparison.json
lines.append("\n--- 2. Structure and Keys of Generated reports/realism_comparison.json ---")
with open(root / "reports" / "realism_comparison.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lines.append(f"Top-level key count: {len(data)}")
for k in data:
    val = data[k]
    if isinstance(val, dict):
        subkeys = list(val.keys())
        lines.append(f"  {k}: dict with keys {subkeys}")
    else:
        lines.append(f"  {k}: {type(val).__name__}")

# 3. Validation against reports/real_range_check.json
lines.append("\n--- 3. Comparison Table with reports/real_range_check.json ---")
with open(root / "reports" / "real_range_check.json", "r", encoding="utf-8") as f:
    rc = json.load(f)

expected_mean = float(rc["patient_level_mean_glucose"]["with_floor"])
expected_tbr = float(rc["time_below_70_with_floor"]["per_patient"])
expected_tar = float(rc["candidate_range_details"]["39 to 501"]["time_above_180_per_patient"])
expected_tar_pooled = float(rc["candidate_range_details"]["39 to 501"]["time_above_180_pooled"])

calc_mean = round(data["mean_glucose"]["real"], 2)
calc_tbr = round(data["time_below_70"]["real"], 4)
calc_tar = round(data["time_above_180"]["real"], 4)
calc_tar_pooled = round(data["time_above_180"]["real_pooled"], 4)

table_header = f"{'Metric':<35} {'Calculated':<12} {'Expected':<12} {'Diff':<12} {'Status'}"
lines.append(table_header)
lines.append("-" * len(table_header))

checks = [
    ("Patient Mean Glucose (mg/dL)", calc_mean, expected_mean, 0.01),
    ("Patient Time Below 70", calc_tbr, expected_tbr, 0.0001),
    ("Patient Time Above 180", calc_tar, expected_tar, 0.0001),
    ("Pooled Time Above 180", calc_tar_pooled, expected_tar_pooled, 0.0001),
]

all_match = True
for name, c_val, e_val, tol in checks:
    diff = abs(c_val - e_val)
    status = "MATCH" if diff <= tol else "MISMATCH"
    if status != "MATCH":
        all_match = False
    lines.append(f"{name:<35} {c_val:<12} {e_val:<12} {diff:<12.5f} {status}")

if all_match:
    lines.append("\nVerification Result: PASS (all real metrics match reports/real_range_check.json exactly)")
else:
    lines.append("\nVerification Result: FAIL (metrics differ from reports/real_range_check.json)")

output = "\n".join(lines) + "\n"
log_path = root / "reports" / "qa" / "logs" / "item2.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(output, encoding="utf-8")
print(output)
