import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent

with open(root / "reports" / "real_range_check.json", "r", encoding="utf-8") as f:
    stats = json.load(f)

# 1. Update docs/REAL_DATA.md
real_data_path = root / "docs" / "REAL_DATA.md"
content = real_data_path.read_text(encoding="utf-8")
old_para = (
    "  * Floor and ceiling readings at these boundaries are valid truncated measurements. "
    "Specifically, 329 readings strictly at the 39.6 mg/dL floor are kept in the dataset "
    "and marked with a boolean censored flag to indicate they hit the sensor physical measurement limit."
)
new_para = (
    f"  * Under the project's valid range of 40 to 500 mg/dL, {stats['readings_at_floor']} readings "
    f"at the sensor's lower limit ({stats['floor_value_mgdl']} mg/dL, {stats['floor_value_mmol']} mmol/L) "
    f"were excluded; {stats['readings_above_400']} readings above 400 mg/dL (maximum {int(stats['maximum_glucose'])}) were kept."
)
if old_para in content:
    content = content.replace(old_para, new_para)
    real_data_path.write_text(content, encoding="utf-8")
    print("Updated docs/REAL_DATA.md")
else:
    print("Target paragraph in docs/REAL_DATA.md not found, checking alternatives...")

# 2. Update docs/REALISM.md
realism_path = root / "docs" / "REALISM.md"
content = realism_path.read_text(encoding="utf-8")
old_line = "| Time Above 180 (%) | 0.1963 | 0.6861 |"
new_line = "| Time Above 180 (% patient-level average) | 0.1963 | 0.6861 |"
if old_line in content:
    content = content.replace(old_line, new_line)

note_target = "## Changes a new synthetic cohort needs"
range_note = (
    f"### Sensor Limits and Valid Range\n"
    f"Under the valid range of 40 to 500 mg/dL, {stats['readings_at_floor']} readings at the sensor's lower limit "
    f"({stats['floor_value_mgdl']} mg/dL, {stats['floor_value_mmol']} mmol/L) were excluded; "
    f"{stats['readings_above_400']} readings above 400 mg/dL (maximum {int(stats['maximum_glucose'])}) were kept. "
    f"Time above 180 is defined as the patient-level average (19.63% in real vs 68.61% in synthetic; "
    f"pooled share is 18.95% in real).\n\n"
)
if "### Sensor Limits and Valid Range" not in content and note_target in content:
    content = content.replace(note_target, range_note + note_target)
    realism_path.write_text(content, encoding="utf-8")
    print("Updated docs/REALISM.md")

# 3. Update README.md
readme_path = root / "README.md"
content = readme_path.read_text(encoding="utf-8")
old_readme_line = (
    "- The synthetic data differ from the real cohort in glucose level: mean glucose is 219.30 mg/dL "
    "in synthetic vs 141.01 mg/dL in the real cohort; time above 180 is 68.6% in synthetic vs 19.6% "
    "in the real cohort (from `reports/realism_comparison.json`, verified by `scripts/verify_real_independent.py`)."
)
new_readme_line = (
    "- The synthetic data differ from the real cohort in glucose level: mean glucose is 219.30 mg/dL "
    "in synthetic vs 141.01 mg/dL in the real cohort; time above 180 (patient-level average) is 68.6% "
    "in synthetic vs 19.6% in the real cohort (from `reports/realism_comparison.json`, verified by `scripts/verify_real_independent.py`). "
    f"In the real dataset under the 40 to 500 mg/dL range, {stats['readings_at_floor']} readings at the sensor's lower limit "
    f"({stats['floor_value_mgdl']} mg/dL, {stats['floor_value_mmol']} mmol/L) were excluded; "
    f"{stats['readings_above_400']} readings above 400 mg/dL (maximum {int(stats['maximum_glucose'])}) were kept (from `reports/real_range_check.json`)."
)
if old_readme_line in content:
    content = content.replace(old_readme_line, new_readme_line)
    readme_path.write_text(content, encoding="utf-8")
    print("Updated README.md")

# 4. Update docs/demo/numbers_for_video.md
video_path = root / "docs" / "demo" / "numbers_for_video.md"
content = video_path.read_text(encoding="utf-8")
if "## Realism Comparison" not in content:
    video_addition = (
        "\n## Realism Comparison\n"
        "* \"Time above 180 mg/dL (patient-level average) is 19.6% in the real cohort vs 68.6% in the synthetic cohort.\" (from `reports/realism_comparison.json` and `reports/real_range_check.json`, cohort comparison)\n"
        f"* \"In the real dataset, {stats['readings_at_floor']} readings at the sensor's lower limit "
        f"({stats['floor_value_mgdl']} mg/dL, {stats['floor_value_mmol']} mmol/L) were excluded; "
        f"{stats['readings_above_400']} readings above 400 mg/dL (maximum {int(stats['maximum_glucose'])}) were kept.\" (from `reports/real_range_check.json`, real data check)\n"
    )
    content += video_addition
    video_path.write_text(content, encoding="utf-8")
    print("Updated docs/demo/numbers_for_video.md")

print("Wording update complete.")
