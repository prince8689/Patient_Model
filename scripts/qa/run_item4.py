import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

lines = []
lines.append("=== Item 4: Demo Video Numbers Verification ===")

target_file = root / "docs" / "demo" / "numbers_for_video.md"
content = target_file.read_text(encoding="utf-8")

lines.append("\n--- 1. Verification of Requirements in docs/demo/numbers_for_video.md ---")

# Check 1: row-level label for 41.0% precision and 91.4% recall
if "row-level precision drops to 41.0% with recall on spike rows 91.4%" in content:
    lines.append("Check 1 (Medium band row-level precision 41.0% and recall 91.4%): PASS")
else:
    lines.append("Check 1 (Medium band row-level precision 41.0% and recall 91.4%): FAIL")

# Check 2: 'captures 91.4% of events' replaced by 'recall on spike rows 91.4%'
if "captures 91.4% of events" not in content and "recall on spike rows 91.4%" in content:
    lines.append("Check 2 ('recall on spike rows 91.4%' present and old phrasing removed): PASS")
else:
    lines.append("Check 2 ('recall on spike rows 91.4%'): FAIL")

# Check 3: Event-level recall check in reports (clinical utility)
clin_reports = list(root.glob("reports/*clinical*.json")) + list(root.glob("reports/*utility*.json"))
lines.append(f"Check 3 (Event-level clinical utility recall reports): Found {len(clin_reports)} files")
if not clin_reports:
    lines.append("  Finding: reports/clinical_utility.json was not saved in repository reports.")
    lines.append("  Documented in file note: 'event-level recall from clinical utility reports was not saved in reports'.")

# Check 4: Forecast coverage 80.0% calibration split wording
expected_forecast_wording = "on the validation split used to calibrate the intervals; held-out forecast test metrics were not saved"
if expected_forecast_wording in content:
    lines.append(f"Check 4 (Forecast coverage 80.0% calibration split phrase): PASS")
else:
    lines.append(f"Check 4 (Forecast coverage 80.0% calibration split phrase): FAIL")

lines.append("\n--- 2. Final Content of docs/demo/numbers_for_video.md ---")
lines.append(content.strip())

output = "\n".join(lines) + "\n"

log_file = root / "reports" / "qa" / "logs" / "item4.txt"
log_file.write_text(output, encoding="utf-8")

print(output)
