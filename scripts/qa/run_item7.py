import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent

def run_cmd(cmd, cwd=None):
    if cwd is None:
        cwd = str(root)
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.stdout.strip() + ("\n" + res.stderr.strip() if res.stderr.strip() else "")

lines = []
lines.append("=== Item 7: Final Commit, Tag, and Verification Suite ===")

lines.append("\n--- 1. Git rev-parse HEAD for main and fresh clone ---")
h_main = run_cmd("git rev-parse HEAD", cwd=r"d:\Patient_Model")
h_clone = run_cmd("git rev-parse HEAD", cwd=r"d:\fresh_test_clone")
lines.append(f"Main HEAD:  {h_main}")
lines.append(f"Clone HEAD: {h_clone}")
lines.append(f"Status: {'EQUAL (PASS)' if h_main == h_clone else 'NOT EQUAL (FAIL)'}")

lines.append("\n--- 2. Fresh clone test suite (python -m pytest -q -rs --durations=15 -p no:cacheprovider) ---")
lines.append(run_cmd(r"..\Patient_Model\.venv\Scripts\python.exe -m pytest -q -rs --durations=15 -p no:cacheprovider", cwd=r"d:\fresh_test_clone"))

lines.append("\n--- 3. Main folder targeted test suite ---")
lines.append(run_cmd(r".\.venv\Scripts\python.exe -m pytest tests/test_audit_readme_numbers.py tests/test_protected_files.py tests/test_real_data.py tests/test_app_smoke.py", cwd=r"d:\Patient_Model"))

lines.append("\n--- 4. Tag submission-v1 verification ---")
lines.append(f"Tag submission-v1 object: {run_cmd('git rev-parse submission-v1', cwd=r'd:\Patient_Model')}")

lines.append("\n--- 5. Final git log --oneline -5 ---")
lines.append(run_cmd("git log --oneline -5", cwd=r"d:\Patient_Model"))

lines.append("\n--- 6. Final git status -sb ---")
lines.append(run_cmd("git status -sb", cwd=r"d:\Patient_Model"))

output = "\n".join(lines) + "\n"
out_path = root / "reports" / "qa" / "logs" / "item7.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(output)

print("Item 7 logged successfully.")
