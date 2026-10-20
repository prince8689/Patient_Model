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
    return out

lines = []
lines.append("=== Item 2: Verification of Presentation and Architecture Files ===")

target_files = [
    "docs/architecture.pdf",
    "docs/DiaTwin_presentation.pdf",
    "docs/DiaTwin_presentation.pptx",
]

lines.append("\n--- 1. Disk Existence and Sizes ---")
all_exist = True
for tf in target_files:
    p = root / tf
    if p.exists():
        size = p.stat().st_size
        lines.append(f"EXISTS: {tf} ({size} bytes)")
    else:
        lines.append(f"MISSING: {tf}")
        all_exist = False

lines.append("\n--- 2. Git Tracking Verification (git ls-files) ---")
git_ls = run_cmd("git ls-files docs/*.pdf docs/*.pptx")
lines.append(git_ls)

tracked_files = [line.strip().replace("\\", "/") for line in git_ls.splitlines() if line.strip()]
all_tracked = True
for tf in target_files:
    if tf in tracked_files:
        lines.append(f"TRACKED: {tf}")
    else:
        lines.append(f"NOT TRACKED: {tf}")
        all_tracked = False

lines.append("\n--- Summary ---")
if all_exist and all_tracked:
    lines.append("Item 2 Result: PASS")
else:
    lines.append("Item 2 Result: FAIL")

output = "\n".join(lines) + "\n"
log_path = root / "reports" / "qa" / "logs" / "item2.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(output, encoding="utf-8")
print(output)

if not (all_exist and all_tracked):
    sys.exit(1)
