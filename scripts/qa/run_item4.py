from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent.parent.parent

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(root))
    out = res.stdout.strip()
    if res.stderr.strip():
        if out:
            out += "\n"
        out += res.stderr.strip()
    return res.returncode, out

lines = []
lines.append("=== Item 4: Number Audit on README and Documentation ===")

# 1. Run audit_readme_numbers.py
lines.append("\n--- 1. Execution of scripts/audit_readme_numbers.py ---")
code1, out1 = run_cmd(".\\.venv\\Scripts\\python scripts/audit_readme_numbers.py")
lines.append(out1)
lines.append(f"Exit code: {code1}")

# Check summary line
has_zero_issues = "0 MISMATCH, 0 NO SOURCE" in out1

# 2. Run unit tests in tests/test_audit_readme_numbers.py
lines.append("\n--- 2. Execution of tests/test_audit_readme_numbers.py ---")
code2, out2 = run_cmd(".\\.venv\\Scripts\\python -m pytest -q -p no:cacheprovider tests/test_audit_readme_numbers.py")
lines.append(out2)
lines.append(f"Exit code: {code2}")

lines.append("\n--- Summary ---")
if code1 == 0 and code2 == 0 and has_zero_issues:
    lines.append("Item 4 Result: PASS")
else:
    lines.append("Item 4 Result: FAIL")

output = "\n".join(lines) + "\n"
log_path = root / "reports" / "qa" / "logs" / "item4.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(output, encoding="utf-8")
print(output)

if code1 != 0 or code2 != 0 or not has_zero_issues:
    sys.exit(1)
