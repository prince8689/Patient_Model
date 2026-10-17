import subprocess

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip() + ("\n" + res.stderr.strip() if res.stderr.strip() else "")

lines = []
lines.append("=== Item 2: Real-data Range Wording and Number Audit ===")
lines.append("\n--- a. Output of scripts/real_range_check.py (reports/real_range_check.json) ---")
lines.append(run_cmd(r".\.venv\Scripts\python.exe scripts/real_range_check.py"))

lines.append("\n--- b. Lines changed in docs/REAL_DATA.md, docs/REALISM.md, README.md, docs/demo/numbers_for_video.md ---")
lines.append(run_cmd("git diff docs/REAL_DATA.md docs/REALISM.md README.md docs/demo/numbers_for_video.md"))

lines.append("\n--- c. Number audit summary ---")
lines.append(run_cmd(r".\.venv\Scripts\python.exe scripts/audit_readme_numbers.py"))

lines.append("\n--- Number audit unit test ---")
lines.append(run_cmd(r".\.venv\Scripts\python.exe -m pytest tests/test_audit_readme_numbers.py"))

output = "\n".join(lines) + "\n"
with open("reports/qa/logs/item2.txt", "w", encoding="utf-8") as f:
    f.write(output)

print("Item 2 logged successfully.")
