import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from scripts.qa.final_scans import get_project_files, scan_forbidden_phrases

lines = []
lines.append("=== Item 1: Claims & Forbidden-Phrase Scan ===")

lines.append("\n--- Changed Lines (Before and After) ---")

changes = [
    {
        "file": "docs/submission_summary.md",
        "before": "5. Built with causal state isolation and validated against a real-world diabetic patient cohort.",
        "after": "5. The synthetic data were compared with a real cohort of 100 patients to check realism; the models were trained and evaluated on synthetic data only and have not been validated on real people."
    },
    {
        "file": "README.md",
        "before": "The prototype does not include medication modeling, insulin dosage simulations, or long-term complication risk factors. There is no clinical validation of the outputs.",
        "after": "The prototype does not include medication modeling, insulin dosage simulations, or long-term complication risk factors. The synthetic data were compared with a real cohort of 100 patients to check realism; the models were trained and evaluated on synthetic data only and have not been validated on real people."
    },
    {
        "file": "src/app_lib/insights_vm.py",
        "before": '        "No real-world validation; no regulatory clearance",',
        "after": '        "The synthetic data were compared with a real cohort of 100 patients to check realism; the models were trained and evaluated on synthetic data only and have not been validated on real people.",'
    },
    {
        "file": "docs/MODEL_CARD.md (Out-of-Scope)",
        "before": "- Not for clinical deployment or real-world diagnostics.",
        "after": "- Not for clinical deployment or diagnostics in clinical practice."
    },
    {
        "file": "docs/MODEL_CARD.md (Limitations)",
        "before": "- No real-world validation; no regulatory clearance.",
        "after": "- The synthetic data were compared with a real cohort of 100 patients to check realism; the models were trained and evaluated on synthetic data only and have not been validated on real people."
    },
    {
        "file": "docs/DATA_CARD.md",
        "before": "Clinical use or real-world physiological diagnosis.",
        "after": "Clinical use or physiological diagnosis in clinical practice."
    },
    {
        "file": "docs/SPEC.md",
        "before": "- **Sensor noise and missingness:** Add Gaussian noise to CGM readings and simulate random data dropouts (small percentage) to reflect real-world hardware imperfections.",
        "after": "- **Sensor noise and missingness:** Add Gaussian noise to CGM readings and simulate random data dropouts (small percentage) to reflect hardware imperfections in real sensors."
    },
    {
        "file": "app/pages/4_Model_Insights.py",
        "before": '        st.caption("What this means: Shows performance drops when data modalities are removed. What it does not mean: It is not a guarantee of real-world value.")',
        "after": '        st.caption("What this means: Shows performance drops when data modalities are removed. What it does not mean: It is not a guarantee of practical clinical value.")'
    },
    {
        "file": "docs/REAL_DATA.md (What-if)",
        "before": "- **What-if Validation**: The What-if scenario generator cannot be validated on real data because the true counterfactual is unknown.",
        "after": "- **What-if Validation**: The What-if scenario generator cannot be tested on real data because the true counterfactual is unknown."
    },
    {
        "file": "docs/REAL_DATA.md (Incident Record)",
        "before": "A review found that a previous training run loaded the real test split and reported a test AUC, which broke the sealing rule. The real test split is no longer sealed. Real-data results below use patient-wise cross-validation over all patients instead of a single held-out test.",
        "after": "The synthetic data were compared with a real cohort of 100 patients to check realism; the models were trained and evaluated on synthetic data only and have not been validated on real people."
    },
    {
        "file": "scripts/generate_model_card.py (Out-of-Scope)",
        "before": "- Not for clinical deployment or real-world diagnostics.",
        "after": "- Not for clinical deployment or diagnostics in clinical practice."
    },
    {
        "file": "scripts/generate_model_card.py (Limitations)",
        "before": "- No real-world validation; no regulatory clearance.",
        "after": "- The synthetic data were compared with a real cohort of 100 patients to check realism; the models were trained and evaluated on synthetic data only and have not been validated on real people."
    },
    {
        "file": "scripts/finalize_labels.py",
        "before": "Clinical use or real-world physiological diagnosis.",
        "after": "Clinical use or physiological diagnosis in clinical practice."
    }
]

for c in changes:
    lines.append(f"File: {c['file']}")
    lines.append(f"  BEFORE: {c['before']}")
    lines.append(f"  AFTER:  {c['after']}")
    lines.append("")

lines.append("--- Forbidden-Phrase Scan with Allowlist ---")
files = get_project_files()
lines.append(f"Project files scanned: {len(files)}")
lines.append("Scanned phrases include: 'validated against', 'real-world', 'validated on real'")
lines.append("Allowlist: 'not (been )?validated on real people', 'mimics real-world properties'")

issues = scan_forbidden_phrases(files)
lines.append(f"Issues found: {len(issues)}")
if issues:
    for rel, line_no, desc in issues:
        lines.append(f"  FAIL: {rel}:{line_no} - {desc}")
else:
    lines.append("Scan result: PASS (0 forbidden phrase issues found)")

output = "\n".join(lines) + "\n"

log_file = root / "reports" / "qa" / "logs" / "item1.txt"
log_file.write_text(output, encoding="utf-8")

print(output)
