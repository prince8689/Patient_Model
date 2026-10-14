# Hosting Plan for Streamlit Community Cloud

This document outlines the deployment strategy, architecture constraints, and step-by-step procedures for hosting DiaTwin on Streamlit Community Cloud.

## Constraints & Architecture

1. **No Git LFS**:
   Streamlit Community Cloud does not support Git LFS pointer resolution during automated build steps. Model files must be standard git objects if committed, or loaded from an external artifact store.
2. **Binary Normalization**:
   To preserve exact SHA-256 hashes across Windows, Linux, and macOS checkouts, `*.joblib` files are marked as binary (`-text`) in `.gitattributes`.
3. **Model Artifact Sizes**:
   The three frozen joblib models require minimal storage:
   - `models/calibrator_v1.joblib`: 3,623 bytes (3.54 KB)
   - `models/xgb_v1.joblib`: 274,527 bytes (268.09 KB)
   - `models/forecaster_v1.joblib`: 2,990,859 bytes (2.85 MB)
   - Total binary size: 3,269,009 bytes (3.12 MB).
4. **Measured Resource Footprint**:
   - Streamlit headless cold startup to responsive health endpoint: 2.59 seconds.
   - Peak memory consumption of the active process tree: 79.68 MB.

## Option A: Deploying with Precomputed Demo Bundle (No Binaries in Git)

In this mode, no model binaries are committed to the repository. The application runs completely from the precompiled insights bundle and demo patient wearable recordings.

1. Ensure environment variable `DIATWIN_DEMO_BUNDLE=1` is configured in Streamlit Cloud Settings (or left as default in `configs/config.yaml`).
2. The core exploratory workflows operate without model loading:
   - Patient List: Displays 40 synthetic patients.
   - Live Twin: Replays 24-hour wearable histories and visualizes precomputed forecasts.
   - What-if Simulator: Evaluates lifestyle scenarios using precomputed projections.
   - Model Insights: Presents static model metrics and evaluation figures.
   - About: Displays architecture, glossary, and verified limitation statements.
3. The custom User Data Entry page gracefully displays:
   `Available when run locally (run python scripts/run_pipeline.py)`
   ensuring visitors understand local execution is required for arbitrary data inference.

## Option B: Deploying with Committed Model Binaries (Owner Decision)

If the repository owner decides to commit the three joblib models directly to git (under 3.2 MB total), the following procedure must be followed:

### 1. Update .gitignore Exceptions
In `.gitignore`, add explicit exceptions for the three frozen joblib files:
```gitignore
# Keep generic joblib ignored
models/*.joblib

# Explicit exceptions for the three frozen artifacts
!models/calibrator_v1.joblib
!models/xgb_v1.joblib
!models/forecaster_v1.joblib
```

### 2. Verify .gitattributes Binary Marking
Ensure `.gitattributes` contains:
```gitattributes
*.joblib -text
```

### 3. Add and Commit Artifacts
```bash
git add -f models/calibrator_v1.joblib models/xgb_v1.joblib models/forecaster_v1.joblib
git add .gitignore .gitattributes
git commit -m "Include frozen model artifacts for cloud deployment"
```

### 4. Verify Hashes in a Fresh Checkout
After cloning, run the verification script to confirm all hashes match the frozen manifests:
```bash
python scripts/qa/protected_files.py
```
All manifest entries must report `MATCH`.
