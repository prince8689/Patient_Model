import subprocess

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip()

lines = []
lines.append("=== 1. Git Status ===")
lines.append(run_cmd("git status -sb"))
lines.append("=== 2. Git Log -5 ===")
lines.append(run_cmd("git log --oneline -5"))
lines.append("=== 3. Git Remote ===")
remote = run_cmd("git remote -v")
if remote:
    lines.append(remote)
else:
    lines.append("(empty - no remote configured)")

output = "\n".join(lines) + "\n"
with open("reports/qa/logs/item1.txt", "w", encoding="utf-8") as f:
    f.write(output)

print(output)
