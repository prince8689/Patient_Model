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
lines.append("=== Item 3: README Items Checker Execution and Tests ===")

# 1. Run check_readme_items.py on README.md
lines.append("\n--- 1. Execution of scripts/check_readme_items.py on README.md ---")
code1, out1 = run_cmd(".\\.venv\\Scripts\\python scripts/check_readme_items.py README.md")
lines.append(out1)
lines.append(f"Exit code: {code1}")

# 2. Run pytest on tests/test_check_readme_items.py
lines.append("\n--- 2. Execution of tests/test_check_readme_items.py ---")
code2, out2 = run_cmd(".\\.venv\\Scripts\\python -m pytest -q -p no:cacheprovider tests/test_check_readme_items.py")
lines.append(out2)
lines.append(f"Exit code: {code2}")

lines.append("\n--- Summary ---")
if code1 == 0 and code2 == 0:
    lines.append("Item 3 Result: PASS")
else:
    lines.append("Item 3 Result: FAIL")

output = "\n".join(lines) + "\n"
log_path = root / "reports" / "qa" / "logs" / "item3.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(output, encoding="utf-8")
print(output)

if code1 != 0 or code2 != 0:
    sys.exit(1)
