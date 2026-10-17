# Deployment Guide for Streamlit Community Cloud

This document outlines the deployment configuration for hosting the DiaTwin prototype on Streamlit Community Cloud.

## Deployment Settings

To deploy the application, configure the following settings in the Streamlit Community Cloud console:

* **Repository**: Your GitHub repository URL (e.g., `https://github.com/<owner>/DiaTwin`)
* **Branch**: `main`
* **Main file path**: `app/main.py`
* **Python version**: `3.12`

## App Secrets

In the Advanced Settings dialog of Streamlit Community Cloud, add the following environment variable to the Secrets section:

```toml
DIATWIN_DEMO_BUNDLE = "1"
```

## Dependencies

Streamlit Community Cloud reads dependencies from `app/requirements.txt` when the entrypoint resides in `app/`. The file is identical to `requirements-demo.txt` and contains only lightweight runtime dependencies:

* `streamlit`
* `plotly`
* `pandas`
* `numpy`
* `pyarrow`
* `pyyaml`

Heavy machine learning libraries (`xgboost`, `shap`, `scikit-learn`) and binary model artifacts (`*.joblib`) are not required when running in demo bundle mode. The precomputed states under `demo_bundle/states/` provide the full interactive experience across all core dashboard pages. The experimental user data entry page displays an indicative notice explaining that full custom inference requires a local installation with trained models.
