import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(root))
    return res.stdout.strip() + ("\n" + res.stderr.strip() if res.stderr.strip() else "")

lines = []
lines.append("=== Item 3: Hosted Dependencies and Streamlit Demo Verification ===")

lines.append("\n--- 1. requirements-demo.txt ---")
lines.append((root / "requirements-demo.txt").read_text(encoding="utf-8").strip())

lines.append("\n--- 2. app/requirements.txt ---")
lines.append((root / "app" / "requirements.txt").read_text(encoding="utf-8").strip())

lines.append("\n--- 3. Unit test verifying requirements are identical ---")
lines.append(run_cmd(r".\.venv\Scripts\python.exe -m pytest tests/test_app_smoke.py -k test_requirements_identical"))

lines.append("\n--- 4. List of packages in clean demo_env ---")
lines.append(run_cmd(r".\demo_env\Scripts\python.exe -m pip list"))

lines.append("\n--- 5. Confirm xgboost, shap and scikit-learn are not required ---")
pip_list = run_cmd(r".\demo_env\Scripts\python.exe -m pip list").lower()
for pkg in ["xgboost", "shap", "scikit-learn"]:
    present = pkg in pip_list
    lines.append(f"  {pkg} present in demo_env: {present} (Required: False)")

lines.append("\n--- 6. AppTest on all 5 pages and user data entry page with DIATWIN_DEMO_BUNDLE=1 ---")
lines.append(run_cmd(r".\demo_env\Scripts\python.exe scripts/test_demo_apptest.py"))

lines.append("\n--- 7. .streamlit/config.toml ---")
lines.append((root / ".streamlit" / "config.toml").read_text(encoding="utf-8").strip())

lines.append("\n--- 8. docs/DEPLOYMENT.md ---")
lines.append((root / "docs" / "DEPLOYMENT.md").read_text(encoding="utf-8").strip())

output = "\n".join(lines) + "\n"
with open(root / "reports" / "qa" / "logs" / "item3.txt", "w", encoding="utf-8") as f:
    f.write(output)

print("Item 3 execution logged successfully.")
