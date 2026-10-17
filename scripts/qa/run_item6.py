import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent

lines = []
lines.append("=== Item 6: Demo Video Material Verification ===")

lines.append("\n--- 1. Verification of Demo Moment (Patient P007 at 2026-01-03 21:50) ---")
state_file = root / "demo_bundle" / "states" / "P007_20260103_2150.json"
assert state_file.exists(), f"State file {state_file} does not exist!"

with open(state_file, "r", encoding="utf-8") as f:
    state = json.load(f)

glucose = state["latest_measurement"]["glucose_mgdl"]
band = state["risk"]["band"]
prob = round(state["risk"]["probability_calibrated"], 3)
quantiles_05 = state["forecast"]["quantiles"]["0.5"]
predicted_peak = round(max(quantiles_05), 1)

lines.append(f"State file: demo_bundle/states/P007_20260103_2150.json")
lines.append(f"  Glucose: {glucose} mg/dL (Expected: 191.4 mg/dL) -> {'MATCH' if glucose == 191.4 else 'MISMATCH'}")
lines.append(f"  Band: {band} (Expected: High) -> {'MATCH' if band == 'High' else 'MISMATCH'}")
lines.append(f"  Calibrated Probability: {prob} (Expected: 0.967) -> {'MATCH' if prob == 0.967 else 'MISMATCH'}")
lines.append(f"  Predicted Peak: {predicted_peak} mg/dL (Expected: 302.3 mg/dL) -> {'MATCH' if predicted_peak == 302.3 else 'MISMATCH'}")

lines.append("\n--- 2. Final Content of docs/demo/numbers_for_video.md ---")
video_numbers_file = root / "docs" / "demo" / "numbers_for_video.md"
content = video_numbers_file.read_text(encoding="utf-8")
lines.append(content.strip())

output = "\n".join(lines) + "\n"
out_path = root / "reports" / "qa" / "logs" / "item6.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(output)

print("Item 6 logged successfully.")
