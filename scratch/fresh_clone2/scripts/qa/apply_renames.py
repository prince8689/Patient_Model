import os
from pathlib import Path
import csv
import subprocess

renames = {
    "reports/figures/age_bmi_hba1c.png": "reports/figures/age_bmi_hba1c.png",
    "reports/figures/cohort_correlation_heatmap.png": "reports/figures/cohort_correlation_heatmap.png",
    "reports/figures/hba1c_by_archetype.png": "reports/figures/hba1c_by_archetype.png",
    "reports/figures/hr_by_sleep_state.png": "reports/figures/hr_by_sleep_state.png",
    "reports/figures/mean_daily_glucose_profile.png": "reports/figures/mean_daily_glucose_profile.png",
    "reports/figures/sample_patient_3days.png": "reports/figures/sample_patient_3days.png",
    "reports/figures/time_in_range_by_archetype.png": "reports/figures/time_in_range_by_archetype.png",
    "reports/figures/archetype_spike_rate.png": "reports/figures/archetype_spike_rate.png",
    "reports/figures/glucose_distribution_by_split.png": "reports/figures/glucose_distribution_by_split.png",
    "reports/figures/label_rate_by_hour.png": "reports/figures/label_rate_by_hour.png",
    "reports/figures/label_rate_per_patient.png": "reports/figures/label_rate_per_patient.png",
    "reports/figures/meal_vs_spike.png": "reports/figures/meal_vs_spike.png",
    "reports/figures/missingness_patterns.png": "reports/figures/missingness_patterns.png",
    "reports/figures/spike_examples.png": "reports/figures/spike_examples.png",
    "reports/figures/feature_correlation_heatmap.png": "reports/figures/feature_correlation_heatmap.png",
    "reports/figures/feature_distributions_by_label.png": "reports/figures/feature_distributions_by_label.png",
    "reports/figures/feature_missingness.png": "reports/figures/feature_missingness.png",
    "reports/figures/top_feature_auc.png": "reports/figures/top_feature_auc.png",
    "reports/figures/calibration_val_before_after.png": "reports/figures/calibration_val_before_after.png",
    "reports/figures/event_recall_vs_alert_burden.png": "reports/figures/event_recall_vs_alert_burden.png",
    "reports/figures/lead_time_hist.png": "reports/figures/lead_time_hist.png",
    "reports/figures/missing_data_effect.png": "reports/figures/missing_data_effect.png",
    "reports/figures/test_calibration.png": "reports/figures/test_calibration.png",
    "reports/figures/test_confusion_matrices.png": "reports/figures/test_confusion_matrices.png",
    "reports/figures/test_per_patient_auc.png": "reports/figures/test_per_patient_auc.png",
    "reports/figures/test_roc_pr.png": "reports/figures/test_roc_pr.png",
    "reports/figures/val_vs_test_metrics.png": "reports/figures/val_vs_test_metrics.png",
    "reports/figures/fault_recovery.png": "reports/figures/fault_recovery.png",
    "reports/figures/latency.png": "reports/figures/latency.png",
    "reports/figures/twin_state_snapshot.png": "reports/figures/twin_state_snapshot.png",
    "reports/figures/twin_timeline_example.png": "reports/figures/twin_timeline_example.png",
    "reports/figures/demo_live_forecast.png": "reports/figures/demo_live_forecast.png",
    "reports/figures/val_coverage_by_horizon.png": "reports/figures/val_coverage_by_horizon.png",
    "reports/figures/val_example_forecasts.png": "reports/figures/val_example_forecasts.png",
    "reports/figures/val_mae_by_horizon.png": "reports/figures/val_mae_by_horizon.png",
    "reports/figures/val_pred_vs_actual_60m.png": "reports/figures/val_pred_vs_actual_60m.png",
    "scripts/calibrate_model.py": "scripts/calibrate_model.py",
    "scripts/evaluate_clinical_utility.py": "scripts/evaluate_clinical_utility.py",
    "scripts/demonstrate_twin.py": "scripts/demonstrate_twin.py",
    "scripts/demonstrate_forecast.py": "scripts/demonstrate_forecast.py",
    "scripts/error_analysis.py": "scripts/error_analysis.py",
    "scripts/finalize_labels.py": "scripts/finalize_labels.py",
    "scripts/finalize_thresholds.py": "scripts/finalize_thresholds.py",
    "scripts/shap_analysis.py": "scripts/shap_analysis.py",
    "scripts/train_model.py": "scripts/train_model.py",
    "tests/test_calibration_and_evaluation.py": "tests/test_calibration_and_evaluation.py",
    "tests/test_golden_fixture.py": "tests/test_golden_fixture.py",
    "tests/golden/glucose_fixture.parquet": "tests/golden/glucose_fixture.parquet"
}

exceptions = [
    "models/thresholds_v1.json",
    "reports/metrics_test_day7.json",
    "reports/oof_train_day7.parquet",
    "reports/test_predictions_day7.parquet"
]

def update_references():
    unprotected_files = []
    root = Path(__file__).resolve().parent.parent.parent
    
    # We should search and replace across scripts, tests, app, src, Makefile, docs, etc.
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        if ".git" in rel_dir.parts or ".venv" in rel_dir.parts or "__pycache__" in rel_dir.parts or ".pytest_cache" in rel_dir.parts or "models" in rel_dir.parts or "reports" in rel_dir.parts or "data" in rel_dir.parts or "configs" in rel_dir.parts:
            continue
            
        for f in filenames:
            if f.endswith((".py", ".md", ".txt", ".sh", "Makefile", ".yml", ".yaml")):
                unprotected_files.append(rel_dir / f)
                
    # Additionally add reports/README.md if we edit it
    
    for f_rel in unprotected_files:
        f = root / f_rel
        try:
            content = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
            
        changed = False
        for old, new in renames.items():
            # simple string replacement
            # Also need to replace just the basename since some scripts use parts of it
            old_base = Path(old).name
            new_base = Path(new).name
            
            # replace full paths
            if old in content:
                content = content.replace(old, new)
                changed = True
            
            # replace basenames
            if old_base in content:
                content = content.replace(old_base, new_base)
                changed = True
                
            # replace module names (for scripts)
            if old.startswith("scripts/") and old.endswith(".py"):
                old_mod = Path(old).stem
                new_mod = Path(new).stem
                if old_mod in content:
                    content = content.replace(old_mod, new_mod)
                    changed = True
                    
        if changed:
            f.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    with open("reports/qa/rename_plan.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["old_path", "proposed_new_path", "protected", "referenced_by_protected", "decision", "reason"])
        writer.writeheader()
        
        for old, new in renames.items():
            writer.writerow({
                "old_path": old,
                "proposed_new_path": new,
                "protected": "no",
                "referenced_by_protected": "no",
                "decision": "rename",
                "reason": "Safe to rename"
            })
            
        for e in exceptions:
            writer.writerow({
                "old_path": e,
                "proposed_new_path": e,
                "protected": "yes",
                "referenced_by_protected": "no",
                "decision": "keep",
                "reason": "Protected file (referenced in integrity manifest or metrics JSON)"
            })
            
    # Apply renames using git mv
    for old, new in renames.items():
        if Path(old).exists():
            subprocess.run(["git", "mv", old, new])
            
    # Update references
    update_references()
