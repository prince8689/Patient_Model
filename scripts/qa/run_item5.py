import os
import re
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
clone_dir = Path("d:/fresh_test_clone")

def remove_dir_robust(path: Path):
    if path.exists():
        subprocess.run(f'cmd /c "rmdir /s /q \"{path}\""', shell=True)
        if path.exists():
            subprocess.run(f'powershell -Command "Remove-Item -Recurse -Force \"{path}\""', shell=True)

def run_cmd(cmd, cwd=root):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(cwd))
    out = res.stdout.strip()
    if res.stderr.strip():
        if out:
            out += "\n"
        out += res.stderr.strip()
    return res.returncode, out

lines = []
lines.append("=== Item 5: Git Commit, Selective Tests, Clone Validation, and Tagging ===")

# 1. Stage modified and new files if any
lines.append("\n--- 1. Git Add & Status Check ---")
add_cmd = (
    "git add "
    "README.md "
    "docs/architecture.pdf "
    "docs/DiaTwin_presentation.pdf "
    "docs/DiaTwin_presentation.pptx "
    "scripts/check_readme_items.py "
    "tests/test_check_readme_items.py "
    "scripts/audit_readme_numbers.py "
    "tests/test_audit_readme_numbers.py "
    "scripts/qa/run_item1.py "
    "scripts/qa/run_item2.py "
    "scripts/qa/run_item3.py "
    "scripts/qa/run_item4.py "
    "scripts/qa/run_item5.py"
)
code, out = run_cmd(add_cmd)
lines.append(f"Add exit code: {code}")
if out:
    lines.append(out)

code_diff, diff_out = run_cmd("git diff --cached --stat")
if diff_out:
    lines.append("\n--- 2. Git Commit ---")
    commit_cmd = 'git commit -m "Add competition submission sections to README, presentation artifacts, and verification tools"'
    code_c, out_c = run_cmd(commit_cmd)
    lines.append(f"Commit exit code: {code_c}")
    lines.append(out_c)
else:
    lines.append("\n--- 2. Git Commit ---")
    lines.append("Working tree already committed at current HEAD.")
    _, head_commit = run_cmd("git log -1 --oneline")
    lines.append(f"Current commit: {head_commit}")

# 3. Run selective tests in main folder
lines.append("\n--- 3. Selective Tests in Main Folder ---")
test_cmd = (
    r".\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider "
    r"tests/test_audit_readme_numbers.py tests/test_realism_comparison.py tests/test_app_smoke.py"
)
code_main_tests, out_main_tests = run_cmd(test_cmd)
lines.append(out_main_tests)
lines.append(f"Exit code: {code_main_tests}")

# 4. Create fresh clone
lines.append("\n--- 4. Fresh Clone Setup ---")
remove_dir_robust(clone_dir)

clone_cmd = f"git clone {root.as_posix()} {clone_dir.as_posix()}"
code_clone, out_clone = run_cmd(clone_cmd)
lines.append(out_clone)
lines.append(f"Clone exit code: {code_clone}")

# 5. Compare git rev-parse HEAD for both folders
lines.append("\n--- 5. Commit Hash Comparison ---")
_, head_main = run_cmd("git rev-parse HEAD", cwd=root)
_, head_clone = run_cmd("git rev-parse HEAD", cwd=clone_dir)
lines.append(f"Main folder HEAD:  {head_main}")
lines.append(f"Clone folder HEAD: {head_clone}")
heads_match = (head_main == head_clone) and len(head_main) == 40
lines.append(f"Commit hashes equal: {heads_match}")

# 6. Run full test suite in clone with 6-minute timeout
lines.append("\n--- 6. Test Suite in Fresh Clone (6-min timeout) ---")
venv_python = root / ".venv" / "Scripts" / "python.exe"
clone_test_cmd = [
    str(venv_python),
    "-m",
    "pytest",
    "-q",
    "-rs",
    "-p",
    "no:cacheprovider",
]

t_start = time.time()
timed_out = False
try:
    proc = subprocess.run(
        clone_test_cmd,
        cwd=str(clone_dir),
        capture_output=True,
        text=True,
        timeout=360,
    )
    wall_time = time.time() - t_start
    clone_test_out = proc.stdout.strip()
    if proc.stderr.strip():
        if clone_test_out:
            clone_test_out += "\n"
        clone_test_out += proc.stderr.strip()
    code_clone_tests = proc.returncode
except subprocess.TimeoutExpired:
    timed_out = True
    wall_time = time.time() - t_start
    clone_test_out = "Test execution in clone exceeded 6 minutes timeout."
    code_clone_tests = -1

lines.append(f"Wall time: {wall_time:.2f} seconds")
if timed_out:
    lines.append("Execution status: STOPPED (exceeded 6 minutes)")
else:
    lines.append(f"Exit code: {code_clone_tests}")
lines.append(clone_test_out)

# Parse totals: collected, passed, failed, skipped
summary_match = re.search(r"(\d+)\s+passed", clone_test_out)
passed_count = summary_match.group(1) if summary_match else "unknown"
failed_match = re.search(r"(\d+)\s+failed", clone_test_out)
failed_count = failed_match.group(1) if failed_match else "0"
skipped_match = re.search(r"(\d+)\s+skipped", clone_test_out)
skipped_count = skipped_match.group(1) if skipped_match else "0"

lines.append("\n--- Test Suite Summary in Clone ---")
lines.append(f"Passed: {passed_count}")
lines.append(f"Failed: {failed_count}")
lines.append(f"Skipped: {skipped_count}")
lines.append(f"Wall time: {wall_time:.2f} s")

# 7. Clean up fresh clone
lines.append("\n--- 7. Cleanup Fresh Clone ---")
remove_dir_robust(clone_dir)
lines.append("Fresh clone directory removed.")

# 8. Recreate tag submission-v1 on main
lines.append("\n--- 8. Retag submission-v1 ---")
code_tag, out_tag = run_cmd("git tag -f submission-v1", cwd=root)
lines.append(f"Tag exit code: {code_tag}")
_, tag_verify = run_cmd("git rev-parse submission-v1", cwd=root)
lines.append(f"Tag submission-v1 points to: {tag_verify}")

# 9. Check git status -sb in main
lines.append("\n--- 9. Git Status in Main ---")
code_status, out_status = run_cmd("git status -sb", cwd=root)
lines.append(out_status)
clean_status = "## main" in out_status and len(out_status.splitlines()) == 1
lines.append(f"Status clean: {clean_status}")

# Overall Result
lines.append("\n--- Summary ---")
item5_pass = (
    code_main_tests == 0
    and heads_match
    and not timed_out
    and code_clone_tests == 0
    and failed_count == "0"
    and clean_status
)
if item5_pass:
    lines.append("Item 5 Result: PASS")
else:
    lines.append("Item 5 Result: FAIL")

output = "\n".join(lines) + "\n"
log_path = root / "reports" / "qa" / "logs" / "item5.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(output, encoding="utf-8")
print(output)

if not item5_pass:
    sys.exit(1)
