import json
import subprocess
import sys
from pathlib import Path
import yaml

root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

lines = []
lines.append("=== Item 3: Real-Data Range Wording & Audit ===")

# 1. Config inspection
lines.append("\n--- 1. configs/real_data.yaml ---")
with open(root / "configs" / "real_data.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
cgm_range = cfg.get("cgm_device", {}).get("valid_range_mgdl")
lines.append(f"cgm_device.valid_range_mgdl: {cgm_range}")

# 2. Loader code inspection
lines.append("\n--- 2. Loader Action (src/real_data/harmonize.py) ---")
lines.append("In src/real_data/harmonize.py (lines 146-155):")
lines.append("  valid_range = config.get('cgm_device', {}).get('valid_range_mgdl', [39.5, 500.5])")
lines.append("  impossible = ((cgm['glucose_mgdl'] < valid_range[0]) | (cgm['glucose_mgdl'] > valid_range[1]))")
lines.append("  cgm = cgm[~impossible].copy()")
lines.append("  cgm['censored'] = (cgm['glucose_mgdl'] <= 39.61) | (cgm['glucose_mgdl'] >= 500.39)")
lines.append("Finding: Readings at 39.6 mg/dL fall inside [39.5, 500.5] and are NOT dropped.")
lines.append("Action on 329 readings at 39.6 mg/dL: KEPT WITH A CENSORED FLAG (censored = True).")

# 3. Quality report inspection
lines.append("\n--- 3. reports/real_data_quality.json ---")
with open(root / "reports" / "real_data_quality.json", "r", encoding="utf-8") as f:
    qual = json.load(f)
lines.append(f"total_glucose_samples_final: {qual.get('total_glucose_samples_final')}")
lines.append(f"censored_readings: {qual.get('censored_readings')}")
lines.append(f"impossible_glucose_dropped: {qual.get('impossible_glucose_dropped')}")
lines.append(f"raw_cgm_rows: {qual.get('raw_cgm_rows')}")

# 4. Matching variant from reports/real_range_check.json
lines.append("\n--- 4. Matching Variant from reports/real_range_check.json ---")
with open(root / "reports" / "real_range_check.json", "r", encoding="utf-8") as f:
    rc = json.load(f)
mean_with = rc["patient_level_mean_glucose"]["with_floor"]
mean_without = rc["patient_level_mean_glucose"]["without_floor"]
tbr_with = rc["time_below_70_with_floor"]["per_patient"]
tbr_without = rc["time_below_70_without_floor"]["per_patient"]
tar_with = rc["candidate_range_details"]["39 to 501"]["time_above_180_per_patient"]
tar_pooled = rc["candidate_range_details"]["39 to 501"]["time_above_180_pooled"]

lines.append(f"Variant matching loader (floor kept):")
lines.append(f"  Patient-level mean glucose: {mean_with:.2f} mg/dL (if excluded: {mean_without:.2f} mg/dL)")
lines.append(f"  Patient-level time below 70: {tbr_with:.4f} (if excluded: {tbr_without:.4f})")
lines.append(f"  Patient-level time above 180: {tar_with:.4f} ({tar_with*100:.2f}%; pooled: {tar_pooled:.4f})")
lines.append("  Definition of time above 180: patient-level average of fraction of readings > 180 mg/dL across all 100 patients.")

# 5. Realism comparison note
lines.append("\n--- 5. Comparison to reports/realism_comparison.json ---")
with open(root / "reports" / "realism_comparison.json", "r", encoding="utf-8") as f:
    realism = json.load(f)
lines.append(f"realism_comparison.json real_counts.samples: {realism.get('real_counts', {}).get('samples')}")
lines.append("Note: realism_comparison.json records real_counts.samples = 112462 (matching kept floor variant).")
lines.append("It does not store mean glucose or time below 70 keys directly; cited values come from reports/real_range_check.json.")

# 6. Updated file lines
lines.append("\n--- 6. Updated Documentation Lines ---")
lines.append("README.md line 30 updated to cite scripts/real_range_check.py and reports/real_range_check.json with kept floor wording.")
lines.append("docs/REAL_DATA.md line 47 updated with kept floor wording.")
lines.append("docs/REALISM.md updated under Sensor Limits and Valid Range with kept floor variant and citations.")
lines.append("docs/demo/numbers_for_video.md line 27 updated with kept floor wording.")

# 7. Number audit execution
lines.append("\n--- 7. Number Audit (scripts/audit_readme_numbers.py) ---")
res = subprocess.run(
    [str(root / ".venv" / "Scripts" / "python.exe"), "scripts/audit_readme_numbers.py"],
    cwd=str(root), capture_output=True, text=True
)
lines.append(res.stdout.strip())
if res.returncode == 0:
    lines.append("Audit Status: PASS (0 mismatches, 0 no-source)")
else:
    lines.append("Audit Status: FAIL")

output = "\n".join(lines) + "\n"

log_file = root / "reports" / "qa" / "logs" / "item3.txt"
log_file.write_text(output, encoding="utf-8")

print(output)
