from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parent.parent.parent
readme_path = root / "README.md"
readme_text = readme_path.read_text(encoding="utf-8")

lines = []
lines.append("=== Item 1: README Headings, Sections, and Fill-in Markers Audit ===")

# 1. Print all headings in README.md
lines.append("\n--- Current Headings in README.md ---")
headings = [line for line in readme_text.splitlines() if line.startswith("#")]
for h in headings:
    lines.append(h)

# 2. Check 12 required sections
required_sections = [
    ("Team details", "Prince Maurya (B.Tech, 3rd year). Contact: princemaur7@gmail.com"),
    ("College / Incubator information", "Kashi Institute of Technology, Varanasi"),
    ("Project title", "DiaTwin: a Type 2 diabetes digital twin that fuses EHR and wearable data (Happiest Health Digital Twin Challenge 2026)"),
    ("Problem statement", "glucose monitors report a rise after it has happened"),
    ("Healthcare use case", "dashboard for a Type 2 diabetes care team and a learning tool"),
    ("Technical stack", "Python, pandas, NumPy, scikit-learn, XGBoost, SHAP, Streamlit, Plotly, PyArrow, pytest, Hypothesis, Git"),
    ("AI/ML model and framework details", "XGBoost risk model with causal features"),
    ("Demo video", "https://youtu.be/h401ih8xMYA"),
    ("Open-source license details", "MIT License (see [LICENSE](LICENSE))"),
    ("Architecture diagram", "[docs/architecture.pdf](docs/architecture.pdf)"),
    ("Presentation", "[docs/DiaTwin_presentation.pdf](docs/DiaTwin_presentation.pdf) ([PPTX version](docs/DiaTwin_presentation.pptx))"),
    ("Public accessibility", "All files and links in this repository are publicly accessible without additional permissions"),
]

lines.append("\n--- Verification of 12 Required Sections ---")
all_sections_pass = True
for title, key_phrase in required_sections:
    # Look for matching heading
    pattern = rf"^##\s+.*{re.escape(title)}.*$"
    match_heading = re.search(pattern, readme_text, re.MULTILINE | re.IGNORECASE)
    has_phrase = key_phrase.lower() in readme_text.lower()
    
    if match_heading and has_phrase:
        lines.append(f"PASS: '{title}' heading found and contains expected text.")
    else:
        all_sections_pass = False
        lines.append(f"FAIL: '{title}' (heading found: {bool(match_heading)}, content found: {has_phrase})")

# 3. Check for fill-in markers and placeholders
lines.append("\n--- Check for Fill-in Markers and Placeholders ---")
forbidden_markers = [
    "[LIVE DEMO URL]",
    "[VIDEO URL]",
    "[TO BE FILLED",
    "[Team name]",
    "[YOUTUBE UNLISTED LINK]",
    "[YOUR EMAIL]",
]
markers_found = []
for m in forbidden_markers:
    if m.lower() in readme_text.lower():
        markers_found.append(m)

if markers_found:
    lines.append(f"FAIL: Found markers: {markers_found}")
    all_sections_pass = False
else:
    lines.append("PASS: No fill-in markers or placeholders found.")

# Overall Status
lines.append("\n--- Summary ---")
if all_sections_pass:
    lines.append("Item 1 Result: PASS")
else:
    lines.append("Item 1 Result: FAIL")

output = "\n".join(lines) + "\n"
log_path = root / "reports" / "qa" / "logs" / "item1.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(output, encoding="utf-8")
print(output)

if not all_sections_pass:
    sys.exit(1)
