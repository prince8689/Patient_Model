import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
clone_dir = Path("d:/fresh_test_clone")

def run_cmd(cmd, cwd=str(root)):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    out = res.stdout.strip()
    if res.stderr.strip():
        if out:
            out += "\n"
        out += res.stderr.strip()
    return out

lines = []
lines.append("=== Item 4: Commit, Fresh Clone Verification & Tag Recreation ===")

# 1. Stage and commit
lines.append("\n--- 1. Git Add and Commit ---")
add_out = run_cmd("git add -A")
if add_out:
    lines.append(add_out)

commit_msg = "Restore complete schema in realism comparison, update regenerations and tests"
lines.append(f"Commit message: {commit_msg}")
commit_out = run_cmd(f'git commit -m "{commit_msg}"')
lines.append(commit_out)

# 2. Check git remote
lines.append("\n--- 2. Git Remote Check (must be empty) ---")
remote_out = run_cmd("git remote -v")
lines.append(remote_out if remote_out else "(git remote -v is empty - PASS)")

# 3. Create fresh clone of committed state
lines.append("\n--- 3. Fresh Clone Creation ---")
if clone_dir.exists():
    shutil.rmtree(clone_dir, ignore_errors=True)
    if clone_dir.exists():
        # Fallback with powershell remove
        run_cmd(f"powershell -Command \"Remove-Item -Recurse -Force '{clone_dir}'\"")

clone_out = run_cmd(f"git clone \"{root}\" \"{clone_dir}\"")
lines.append(clone_out if clone_out else f"Cloned {root} into {clone_dir}")

# 4. Compare git rev-parse HEAD for both folders
lines.append("\n--- 4. Commit Hash Verification (git rev-parse HEAD) ---")
main_head = run_cmd("git rev-parse HEAD", cwd=str(root))
clone_head = run_cmd("git rev-parse HEAD", cwd=str(clone_dir))
lines.append(f"Main folder HEAD:  {main_head}")
lines.append(f"Clone folder HEAD: {clone_head}")
if main_head == clone_head:
    lines.append("Equality: EQUAL (PASS)")
else:
    lines.append("Equality: MISMATCH (FAIL)")

# 5. Run pytest in clone folder
lines.append("\n--- 5. Pytest in Fresh Clone (python -m pytest -q -rs -p no:cacheprovider) ---")
python_exe = str(root / ".venv" / "Scripts" / "python.exe")
start_time = time.time()
pytest_cmd = f"\"{python_exe}\" -m pytest -q -rs -p no:cacheprovider"
test_out = run_cmd(pytest_cmd, cwd=str(clone_dir))
wall_time = time.time() - start_time
lines.append(test_out)

# 6. Parse and print summary
lines.append("\n--- 6. Test Suite Execution Summary ---")
lines.append(f"Wall time: {wall_time:.2f} seconds")

# Extract summary line from pytest output
# e.g. "91 passed, 23 skipped, 4 warnings in 120.45s"
summary_match = re.search(r"(=+\s*(?:(\d+)\s+passed)?(?:,\s*(\d+)\s+skipped)?(?:,\s*(\d+)\s+failed)?.*in\s+([\d\.]+s).*)", test_out)
if summary_match:
    lines.append(f"Pytest summary: {summary_match.group(1).strip()}")

# Extract skipped reasons
skipped_reasons = re.findall(r"SKIPPED\s+\[\d+\]\s+([^:]+:\d+:\s*.+)", test_out)
if skipped_reasons:
    lines.append(f"Skipped tests count: {len(skipped_reasons)}")
    lines.append("Skipped reasons:")
    for r in skipped_reasons:
        lines.append(f"  - {r}")
else:
    # Check for short summary reasons
    short_skipped = re.findall(r"SKIP\s+\[\d+\]\s+([^:]+:\d+:\s*.+)", test_out)
    if short_skipped:
        lines.append(f"Skipped tests count: {len(short_skipped)}")
        lines.append("Skipped reasons:")
        for r in short_skipped:
            lines.append(f"  - {r}")

# 7. Delete and recreate tag submission-v1 on the new commit
lines.append("\n--- 7. Tag submission-v1 Recreation ---")
del_tag = run_cmd("git tag -d submission-v1", cwd=str(root))
lines.append(del_tag)
create_tag = run_cmd("git tag submission-v1", cwd=str(root))
lines.append(create_tag if create_tag else "Created tag submission-v1 on new commit")

# 8. Print git status -sb
lines.append("\n--- 8. Git Status -sb ---")
status_sb = run_cmd("git status -sb", cwd=str(root))
lines.append(status_sb)

# 9. Clean up clone folder
shutil.rmtree(clone_dir, ignore_errors=True)

output = "\n".join(lines) + "\n"
log_path = root / "reports" / "qa" / "logs" / "item4.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(output, encoding="utf-8")
print(output)
