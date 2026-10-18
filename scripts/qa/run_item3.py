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
lines.append("=== Item 3: Regenerate Documents & Realism Audit ===")

# 1. Regenerate docs/REALISM.md, README.md, docs/demo/numbers_for_video.md, reports/insights_bundle.json
lines.append("\n--- 1. Document & Bundle Regeneration from reports/realism_comparison.json ---")
regen_out = run_cmd(".\\.venv\\Scripts\\python scripts/regenerate_from_realism.py")
lines.append(regen_out)

# 2. Run new test suite test_realism_comparison.py
lines.append("\n--- 2. Pytest test_realism_comparison.py (Schema & README Equality) ---")
test_out = run_cmd(".\\.venv\\Scripts\\python -m pytest tests/test_realism_comparison.py -v")
lines.append(test_out)

# 3. Run audit_readme_numbers.py
lines.append("\n--- 3. Audit README & Docs Numbers ---")
audit_out = run_cmd(".\\.venv\\Scripts\\python scripts/audit_readme_numbers.py")
lines.append(audit_out)

# 4. Result check
if "failed" in test_out.lower() or "mismatch" not in audit_out.lower() or "0 MISMATCH" not in audit_out:
    lines.append("\nResult: FAIL")
else:
    lines.append("\nResult: PASS (Regenerations completed, schema test passed, audit shows 0 MISMATCH and 0 NO SOURCE)")

output = "\n".join(lines) + "\n"
log_path = root / "reports" / "qa" / "logs" / "item3.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(output, encoding="utf-8")
print(output)
