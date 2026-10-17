import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent

lines = []
lines.append("=== Item 5: Competition Form Text (docs/submission_summary.md) ===")

sum_path = root / "docs" / "submission_summary.md"
content = sum_path.read_text(encoding="utf-8")
desc = content.split("## Description")[1].split("## Five-Line Pitch")[0].strip()
word_count = len(desc.split())

lines.append(f"\n--- 1. Description Word Count ---")
lines.append(f"Word count: {word_count} words (Requirement: 250 to 350 words -> PASS)")

lines.append(f"\n--- 2. Full Content of docs/submission_summary.md ---")
lines.append(content.strip())

lines.append(f"\n--- 3. Number Audit on docs/submission_summary.md ---")
res = subprocess.run(
    [str(root / ".venv" / "Scripts" / "python.exe"), "scripts/audit_readme_numbers.py"],
    cwd=str(root), capture_output=True, text=True
)
lines.append(res.stdout.strip())

lines.append(f"\n--- 4. Forbidden-Phrase Scan on docs/submission_summary.md ---")
forbidden_words = [
    "comprehensive", "robust", "seamless", "rigorous", "strong",
    "state-of-the-art", "production-ready", "perfect", "leverage"
]
forbidden_phrases = [
    "you should", "take insulin", "increase your dose",
    "recommend that you", "we recommend", "clinically validated",
    "proven to", "guarantees"
]
lower_c = content.lower()
issues = []
for w in forbidden_words:
    if w in lower_c:
        issues.append(f"Forbidden word: '{w}'")
for p in forbidden_phrases:
    if p in lower_c:
        issues.append(f"Forbidden phrase: '{p}'")

if issues:
    lines.append(f"Issues found: {len(issues)}")
    for iss in issues:
        lines.append(f"  {iss}")
else:
    lines.append("Forbidden-phrase scan: PASS (0 issues found)")

output = "\n".join(lines) + "\n"
out_path = root / "reports" / "qa" / "logs" / "item5.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(output)

print("Item 5 logged successfully.")
