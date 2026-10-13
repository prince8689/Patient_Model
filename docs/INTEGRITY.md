# Integrity Verification in DiaTwin

To ensure strict compliance with a "Frozen-before-test" protocol and prevent data leakage, DiaTwin employs an end-to-end integrity verification system.

## 1. Frozen Manifests
The model artifacts, critical thresholds, and core pipeline components are cryptographically hashed using SHA256 during the `freeze` milestone of the project. These hashes are stored in JSON manifests:
- `models/FROZEN.json` (Risk Pipeline)
- `models/FORECAST_FROZEN.json` (Forecasting Module)
- `models/WHATIF_FROZEN.json` (What-if Simulation Engine)

## 2. Startup Verification
When the `DiaTwin` engine loader initializes (`src/twin/loader.py`), it automatically reads the manifests and recalculates the SHA256 hash of every tracked file on disk. If any file has been modified since the freeze, a `ValueError` is thrown, halting execution.

## 3. Configuration Auditing
Adding UI configurations and layout instructions (e.g., the `app:` or `insights:` section in `configs/config.yaml`) causes the whole-file hash to diverge from the freeze manifest. To safely allow UI modifications without weakening integrity:
- The loader bypasses the rigid whole-file hash check exclusively for `config.yaml`.
- Instead, it verifies via a section-level check that no value present in the first-freeze config (commit 82c36c0) changed, normalising CRLF to LF before comparing.
- For the forecast and what-if modules, the manifest and the test marker were first committed together (commits 7210b6d and b5f8c07), so freeze-before-test cannot be proven from git for them.
- For the risk model, the freeze commit precedes the test commit.

## 4. UI Dashboard Honesty
The `Model Insights` and `About` pages adhere to a strict "display-only" rule. They do not have access to models or raw data. Instead, they consume a compiled `reports/insights_bundle.json` generated from static report files.

This end-to-end mechanism ensures that the model evaluated is identical to the one in production, while permitting iterative UI and documentation enhancements.
