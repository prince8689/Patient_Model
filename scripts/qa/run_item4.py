import os
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(root))
    return res.stdout.strip() + ("\n" + res.stderr.strip() if res.stderr.strip() else "")

lines = []
lines.append("=== Item 4: Pre-push Hygiene Scan ===")

lines.append("\n--- 1. git check-ignore for .venv, demo_env, scratch, data/external, reports/qa/logs ---")
lines.append(run_cmd("git check-ignore .venv demo_env scratch data/external reports/qa/logs"))

lines.append("\n--- 2. Ten largest tracked files ---")
files = subprocess.run("git ls-files", shell=True, capture_output=True, text=True, cwd=str(root)).stdout.splitlines()
sizes = []
for f in files:
    p = root / f
    if p.exists() and p.is_file():
        sizes.append((p.stat().st_size, f))
sizes.sort(reverse=True)
for s, f in sizes[:10]:
    lines.append(f"  {s:>10} bytes ({s/1024/1024:.2f} MB)  {f}")

lines.append("\n--- 3. Total size from git count-objects -vH ---")
lines.append(run_cmd("git count-objects -vH"))

lines.append("\n--- 4. Scan of tracked files for personal data and local paths (@gmail, Prince, C:\\Users, D:\\) ---")
personal_patterns = ["@gmail", "prince", "c:\\users", "d:\\"]
found_personal = []
text_exts = {".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".html", ".css", ".js"}

for f in files:
    p = root / f
    if not p.exists() or not p.is_file():
        continue
    if p.suffix.lower() not in text_exts:
        continue
    # Exclude scanner itself or known scan command strings in QA scripts
    if "final_scans.py" in f or "run_item4.py" in f:
        continue
    try:
        content = p.read_text(encoding="utf-8", errors="ignore").lower()
        for pat in personal_patterns:
            if pat in content:
                found_personal.append((f, pat))
    except Exception:
        pass

if found_personal:
    lines.append(f"Found {len(found_personal)} occurrences:")
    for f, pat in found_personal:
        lines.append(f"  {f}: contains '{pat}'")
else:
    lines.append("No personal data or local absolute paths found in project files (PASS).")

lines.append("\n--- 5. List of tracked files/lines naming an AI tool or assistant (listed only for owner decision) ---")
ai_patterns = [
    r"\bchatgpt\b", r"\bclaude\b", r"\bcopilot\b", r"\bgemini\b",
    r"\bantigravity\b", r"\bopenai\b", r"\banthropic\b", r"\bcursor\b",
    r"\bgpt-[34]\b", r"\bgpt-4o\b"
]
ai_regex = re.compile("|".join(ai_patterns), re.IGNORECASE)
found_ai = []

for f in files:
    p = root / f
    if not p.exists() or not p.is_file():
        continue
    if p.suffix.lower() not in text_exts:
        continue
    if "run_item4.py" in f:
        continue
    try:
        file_lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, l in enumerate(file_lines, 1):
            m = ai_regex.search(l)
            if m:
                found_ai.append((f, idx, m.group(0), l.strip()))
    except Exception:
        pass

lines.append(f"Total AI tool references found: {len(found_ai)}")
for f, idx, match_word, text in found_ai:
    lines.append(f"  {f}:{idx} [{match_word}]: {text[:100]}")

lines.append("\n--- 6. git ls-files file count (Measure-Object) ---")
lines.append(run_cmd("powershell -Command \"git ls-files | Measure-Object\""))

output = "\n".join(lines) + "\n"
out_path = root / "reports" / "qa" / "logs" / "item4.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(output)

print("Item 4 logged successfully.")
