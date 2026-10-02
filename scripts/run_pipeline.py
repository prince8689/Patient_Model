import argparse
import subprocess
import time
import sys
from pathlib import Path
import json

def run_step(name, script_path, args=None, dry_run=False):
    print(f"\n--- Running: {name} ---")
    if dry_run:
        print(f"[DRY-RUN] python {script_path} {' '.join(args or [])}")
        return 0
    start = time.time()
    cmd = [sys.executable, script_path] + (args or [])
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {name}")
        return e.returncode
    end = time.time()
    print(f"Completed in {end-start:.1f}s")
    return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--from-stage", default="generate_patients")
    parser.add_argument("--to-stage", default="insights_bundle")
    parser.add_argument("--fresh-protocol", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    
    stages = [
        ("generate_patients", "scripts/generate_patients.py", []),
        ("generate_wearable", "scripts/generate_wearable.py", []),
        ("data_quality", "scripts/data_quality_report.py", []),
        ("labels_and_splits", "scripts/build_labels_and_splits.py", []),
        ("features", "scripts/build_features.py", []),
        ("leakage_check", "scripts/leakage_smoke_test.py", []),
        ("train_model", "scripts/train_model.py", []),
        ("calibrate_model", "scripts/calibrate_model.py", []),
        ("finalize_thresholds", "scripts/finalize_thresholds.py", []),
        ("freeze_model", "scripts/freeze_model.py", []),
    ]
    
    # We must ensure test evaluation isn't run if done, unless --force
    root = Path(__file__).resolve().parent.parent
    if (root / "reports" / "TEST_EVAL_DONE.json").exists() and not args.force and not args.fresh_protocol:
        print("TEST_EVAL_DONE exists. Skipping final test eval to protect integrity.")
        allow_test = False
    else:
        allow_test = args.fresh_protocol or args.force
        
    if allow_test:
        stages.append(("final_test_eval", "scripts/final_test_eval.py", ["--allow_test"]))
        
    stages.extend([
        ("shap_analysis", "scripts/shap_analysis.py", []),
        ("clinical_utility", "scripts/evaluate_clinical_utility.py", []),
        ("build_forecast_targets", "scripts/build_forecast_targets.py", []),
        ("train_forecast", "scripts/train_forecast.py", []),
        ("freeze_forecast", "scripts/freeze_forecast.py", []),
    ])
    
    if (root / "reports" / "FORECAST_TEST_DONE.json").exists() and not args.force and not args.fresh_protocol:
        print("FORECAST_TEST_DONE exists. Skipping forecast test eval.")
        allow_forecast_test = False
    else:
        allow_forecast_test = allow_test
        
    if allow_forecast_test:
        stages.append(("evaluate_forecast_val", "scripts/evaluate_forecast_val.py", ["--split", "test", "--allow_test"]))
        
    stages.extend([
        ("fit_population_prior", "scripts/fit_population_prior.py", []),
    ])
    
    if (root / "reports" / "WHATIF_TEST_DONE.json").exists() and not args.force and not args.fresh_protocol:
        print("WHATIF_TEST_DONE exists. Skipping whatif test eval.")
        allow_whatif_test = False
    else:
        allow_whatif_test = allow_test
        
    if allow_whatif_test:
        stages.append(("final_whatif_test_eval", "scripts/final_whatif_test_eval.py", ["--allow_test"]))
        
    stages.extend([
        ("build_demo_bundle", "scripts/build_demo_bundle.py", []),
        ("insights_bundle", "scripts/build_insights_bundle.py", [])
    ])
    
    # Filter stages
    start_idx = 0
    end_idx = len(stages)
    for i, (name, _, _) in enumerate(stages):
        if name == args.from_stage: start_idx = i
        if name == args.to_stage: end_idx = i + 1
        
    for name, script_path, cmd_args in stages[start_idx:end_idx]:
        if run_step(name, str(root / script_path), cmd_args, args.dry_run) != 0:
            print(f"Pipeline failed at stage {name}")
            sys.exit(1)
            
if __name__ == "__main__":
    main()
