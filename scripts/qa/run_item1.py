import json
import subprocess
import sys
from pathlib import Path

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
lines.append("=== Item 1: Realism Comparison File History & Schema Analysis ===")

# 1. git log --oneline -6 for reports/realism_comparison.json
lines.append("\n--- 1. Git Log (Last 6 Commits for reports/realism_comparison.json) ---")
git_log_output = run_cmd("git log --oneline -6 -- reports/realism_comparison.json")
lines.append(git_log_output)

# 2. Keys of the file now (at HEAD)
lines.append("\n--- 2. Keys of reports/realism_comparison.json Now (HEAD) ---")
with open(root / "reports" / "realism_comparison.json", "r", encoding="utf-8") as f:
    current_data = json.load(f)
current_keys = list(current_data.keys())
lines.append(f"Key count: {len(current_keys)}")
lines.append("Keys: " + ", ".join(current_keys))

# 3. Last commit that had mean_glucose and its keys
lines.append("\n--- 3. Keys at Last Commit with mean_glucose (828c337) ---")
show_output = run_cmd("git show 828c337:reports/realism_comparison.json")
old_data = json.loads(show_output)
old_keys = list(old_data.keys())
lines.append(f"Commit: 828c337")
lines.append(f"Key count: {len(old_keys)}")
lines.append("Keys: " + ", ".join(old_keys))

# 4. Grep for realism_comparison in scripts and src
lines.append("\n--- 4. Grep for 'realism_comparison' in scripts and src ---")
grep_output = run_cmd("git grep \"realism_comparison\" scripts/ src/")
lines.append(grep_output)

# 5. Writers identification
lines.append("\n--- 5. Scripts That Write reports/realism_comparison.json ---")
lines.append("1. scripts/compute_realism.py: opens reports/realism_comparison.json with mode 'w'")
lines.append("2. src/real_data/compare.py: opens reports/realism_comparison.json with mode 'w'")

# 6. Explanation of overwrite
lines.append("\n--- 6. Root Cause Explanation of Schema Regression ---")
lines.append(
    "In commit 8118201 ('Implement personalized data entry page, sleep schedule defaults, hosting plan and tests'), "
    "scripts/compute_realism.py was executed to update metrics. That script only calculated 12 keys "
    "(synthetic_use_insulin, real_use_insulin, synthetic_label_prevalence, real_label_prevalence, "
    "synthetic_meal_rise_mean, real_meal_rise_mean, synthetic_gaps, real_gaps, synthetic_counts, "
    "real_counts, synthetic_regression, real_regression) and wrote them directly to reports/realism_comparison.json. "
    "This overwrote the previous 20-key schema from commit 828c337 (which had mean_glucose, std_glucose, cv_glucose, "
    "time_below_70, time_70_180, time_above_180, hour_profile, and individual slot statistics)."
)

output = "\n".join(lines) + "\n"
log_path = root / "reports" / "qa" / "logs" / "item1.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(output, encoding="utf-8")
print(output)
