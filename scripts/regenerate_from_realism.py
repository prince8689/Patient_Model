"""Regenerate documents and bundle from reports/realism_comparison.json.
Committed code that synchronizes docs/REALISM.md, README.md, docs/demo/numbers_for_video.md,
and reports/insights_bundle.json with reports/realism_comparison.json.
"""
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from scripts.build_realism_doc import build_md
from scripts.build_insights_bundle import build_bundle

def regenerate_all():
    root = Path(__file__).resolve().parent.parent
    realism_path = root / "reports" / "realism_comparison.json"
    with open(realism_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Regenerate docs/REALISM.md
    print("Regenerating docs/REALISM.md...")
    build_md()

    # 2. Regenerate README.md sentence on glucose level
    print("Regenerating README.md glucose level sentence...")
    readme_path = root / "README.md"
    readme_content = readme_path.read_text(encoding="utf-8")
    
    synth_mean = f"{data['mean_glucose']['synthetic']:.2f}"
    real_mean = f"{data['mean_glucose']['real']:.2f}"
    synth_tar = f"{data['time_above_180']['synthetic']*100:.1f}%"
    real_tar = f"{data['time_above_180']['real']*100:.1f}%"

    pattern = r"- The synthetic data differ from the real cohort in glucose level:.*"
    replacement = (
        f"- The synthetic data differ from the real cohort in glucose level: mean glucose is {synth_mean} mg/dL "
        f"in synthetic vs {real_mean} mg/dL in the real cohort; time above 180 (patient-level average) is {synth_tar} "
        f"in synthetic vs {real_tar} in the real cohort (from `reports/realism_comparison.json`, verified by "
        f"`scripts/real_range_check.py` and `reports/real_range_check.json`). In the real dataset under the 39.5 to 500.5 mg/dL "
        f"range in `configs/real_data.yaml`, 329 readings at the sensor lower limit (39.6 mg/dL, 2.2 mmol/L) are kept "
        f"with a censored flag; 30 readings above 400 mg/dL (maximum 468) were kept (from `reports/real_range_check.json`)."
    )
    if re.search(pattern, readme_content):
        readme_content = re.sub(pattern, replacement, readme_content)
        readme_path.write_text(readme_content, encoding="utf-8")
        print("Updated README.md")

    # 3. Regenerate docs/demo/numbers_for_video.md
    print("Regenerating docs/demo/numbers_for_video.md...")
    video_path = root / "docs" / "demo" / "numbers_for_video.md"
    video_content = video_path.read_text(encoding="utf-8")
    
    v_line1 = (
        f'* "Time above 180 mg/dL (patient-level average) is {real_tar} in the real cohort vs {synth_tar} '
        f'in the synthetic cohort." (from `reports/realism_comparison.json` and `reports/real_range_check.json`, cohort comparison)'
    )
    v_pattern = r'\* "Time above 180 mg/dL \(patient-level average\) is [0-9\.]+% in the real cohort vs [0-9\.]+% in the synthetic cohort\." \(from `reports/realism_comparison\.json`[^)]*\)'
    if re.search(v_pattern, video_content):
        video_content = re.sub(v_pattern, v_line1, video_content)
        video_path.write_text(video_content, encoding="utf-8")
        print("Updated docs/demo/numbers_for_video.md")

    # 4. Regenerate reports/insights_bundle.json
    print("Regenerating reports/insights_bundle.json...")
    build_bundle()

    print("All regenerations from reports/realism_comparison.json complete.")

if __name__ == "__main__":
    regenerate_all()
