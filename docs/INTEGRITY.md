# Integrity Verification in DiaTwin

To ensure strict compliance with a "Frozen-before-test" protocol and prevent data leakage, DiaTwin employs an end-to-end integrity verification system.

## 1. Frozen Manifests
The model artifacts, critical thresholds, and core pipeline components are cryptographically hashed using SHA256 during the `freeze` phase of the project (Day 7, Day 9, Day 10). These hashes are stored in JSON manifests:
- `models/FROZEN.json` (Risk Pipeline)
- `models/FORECAST_FROZEN.json` (Forecasting Module)
- `models/WHATIF_FROZEN.json` (What-if Simulation Engine)

## 2. Startup Verification
When the `DiaTwin` engine loader initializes (`src/twin/loader.py`), it automatically reads the manifests and recalculates the SHA256 hash of every tracked file on disk. If any file has been modified since the freeze, a `ValueError` is thrown, halting execution.

## 3. Configuration Auditing
Adding UI configurations and layout instructions (e.g., the `app:` or `insights:` section in `configs/config.yaml`) causes the whole-file hash to diverge from the freeze manifest. To safely allow UI modifications without weakening integrity:
- The loader bypasses the rigid whole-file hash check exclusively for `config.yaml`.
- Instead, it delegates verification to `scripts/qa/config_audit.py`.
- The audit script pulls the original `config.yaml` from git history at the exact commit of the freeze.
- It parses both YAML files and verifies that **all frozen-relevant configuration sections** (e.g., `evaluation`, `features`, `forecast`, `paths`, etc.) are deeply identical to their frozen state.
- Only safe, presentation-only top-level sections (like `app` and `insights`) are permitted to be new or modified.

## 4. UI Dashboard Honesty
The `Model Insights` and `About` pages adhere to a strict "display-only" rule. They do not have access to models or raw data. Instead, they consume a compiled `reports/insights_bundle.json` generated from static report files.

This end-to-end mechanism ensures that the model evaluated is identical to the one in production, while permitting iterative UI and documentation enhancements.
