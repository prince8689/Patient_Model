# Hosting Plan for DiaTwin

This document outlines the architecture, deployment process, and dependency strategy for hosting the DiaTwin Streamlit application.

## 1. Binary Artifact Management without Git LFS

Streamlit Community Cloud does not support Git LFS pointers natively without manual hook configuration, and Git LFS bandwidth limits can cause build interruptions. Because the three serialized model files total approximately 3.2 MB (well below GitHub's 100 MB per-file threshold), Git LFS is unnecessary.

### Model Files and Sizes
The three model binaries required for local inference and full testing are:
- `models/calibrator_v1.joblib`: 3.6 KB
- `models/xgb_v1.joblib`: 268.1 KB
- `models/forecaster_v1.joblib`: 2.9 MB

Total size: approximately 3.2 MB.

### Git Attributes Configuration
To prevent git line-ending normalization from corrupting binary files across operating systems, `*.joblib` files are marked as binary in `.gitattributes`:
```text
*.joblib -text
```
This ensures that SHA256 hashes remain identical across Windows, Linux, and macOS checkouts.

### Git Ignore Exceptions
By default, `.gitignore` excludes `models/*.joblib`. To track exactly the three verified model binaries, add exact negate patterns:
```text
!models/xgb_v1.joblib
!models/calibrator_v1.joblib
!models/forecaster_v1.joblib
```
Decision note: Do not commit the binary files in this session; this decision is left to the repository owner.

## 2. Integrity Verification in Fresh Checkouts

When model binaries are included in the repository:
1. Clone the repository into a fresh directory.
2. Run the manifest verification script:
   ```bash
   python scripts/qa/protected_files.py
   ```
3. All files listed in `models/FROZEN.json`, `models/FORECAST_FROZEN.json`, and `models/WHATIF_FROZEN.json` must report `MATCH`.

## 3. Test Execution with Model Binaries

When the three model binaries are present on disk, tests that normally skip with "Frozen models not present in this checkout" will execute:
- `tests/test_user_input.py` (indicative fuzz, parity with engine, driver explainers)
- `tests/test_forecast_model.py`
- `tests/test_twin_parity.py`

In our test suite run with model binaries present, these tests execute in approximately 165 seconds.

## 4. Hosting Execution Modes

The application supports two operating modes:

### Demo Bundle Mode (`DIATWIN_DEMO_BUNDLE=1`)
- Runs without model files or simulation dependencies.
- Serves precomputed trajectories and state snapshots from `demo_bundle/`.
- Suitable for public demo hosting on Streamlit Community Cloud.
- Requires only lightweight dependencies from `requirements-demo.txt`.

### Interactive Evaluation Mode (`DIATWIN_DEMO_BUNDLE=0` or default)
- Loads the frozen pipeline, calibrator, and forecaster models into memory.
- Enables the Personalized Data Entry page (`user_data_entry.py`) to run live inferences on custom profile and glucose data.
- Requires `xgboost`, `scikit-learn`, and `joblib`.
