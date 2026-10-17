import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent

def run_cmd(cmd, cwd=str(root)):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    out = res.stdout.strip()
    if res.stderr.strip():
        if out:
            out += "\n"
        out += res.stderr.strip()
    return out

lines = []
lines.append("=== Item 2: Editor Files & Workspace Clean Up ===")

# 1. git ls-files for editor folders
lines.append("\n--- 1. git ls-files .agent .agents .gemini .cursor .vscode ---")
editor_files = run_cmd("git ls-files .agent .agents .gemini .cursor .vscode")
lines.append(editor_files if editor_files else "(no files found)")

# 2. git rm -r --cached
lines.append("\n--- 2. git rm -r --cached for editor and assistant folders ---")
rm_cmd = "git rm -r --cached .agent .agents .gemini adapters scripts/validate-agents.ps1 scripts/validate-agents.sh"
lines.append(run_cmd(rm_cmd))

# 3. Verify .gitignore
lines.append("\n--- 3. Updated .gitignore ---")
gitignore_content = (root / ".gitignore").read_text(encoding="utf-8")
lines.append(gitignore_content.strip())

# 4. Stage all changes and commit
lines.append("\n--- 4. Git Add and Commit ---")
run_cmd("git add -A")
commit_res = run_cmd('git commit -m "Remove tracked editor and assistant workspace files and update claims"')
lines.append(commit_res)

# 5. Delete and recreate tag submission-v1
lines.append("\n--- 5. Delete and Recreate Tag submission-v1 ---")
del_tag = run_cmd("git tag -d submission-v1")
lines.append(del_tag)
create_tag = run_cmd("git tag submission-v1")
lines.append(create_tag if create_tag else "Created tag submission-v1")

# 6. Verify git ls-files | Select-String 'agent|gemini|cursor' (must be empty)
lines.append("\n--- 6. Verify git ls-files | Select-String 'agent|gemini|cursor' ---")
check_agent = run_cmd("powershell -Command \"git ls-files | Select-String 'agent|gemini|cursor'\"")
if not check_agent:
    lines.append("(empty - PASS)")
else:
    lines.append(f"FAIL - matching files found:\n{check_agent}")

# 7. Print new commit hash
lines.append("\n--- 7. New Commit Hash ---")
new_head = run_cmd("git rev-parse HEAD")
lines.append(new_head)

# 8. Print git status -sb
lines.append("\n--- 8. Git Status -sb ---")
status_sb = run_cmd("git status -sb")
lines.append(status_sb)

output = "\n".join(lines) + "\n"

log_file = root / "reports" / "qa" / "logs" / "item2.txt"
log_file.write_text(output, encoding="utf-8")

print(output)
