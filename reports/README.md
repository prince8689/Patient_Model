# Reports Directory

This directory contains outputs, metrics, and generated artifacts from the pipeline.

The following files retain stage-like naming conventions (e.g., `_day7`) because their names are recorded in the integrity manifests:
- `metrics_test_day7.json`: Contains evaluation metrics from the test set.
- `oof_train_day7.parquet`: Contains out-of-fold predictions from training.
- `test_predictions_day7.parquet`: Contains final predictions on the test set.

Do not rename or modify these files.
