# Demo Numbers for Video Script

When quoting metrics in the video, use the following exact numbers and intervals. 

**Mandatory Phrasing**: You must preface or append quotes with: *"in this synthetic setting"*.

## Risk Model Classification
* "In this synthetic setting, the model achieved a ROC AUC of 0.925 (95% CI: 0.907 - 0.944)." (from `reports/metrics_test_day7.json`, test split)
* "Calibration Error (ECE) is very low at 0.0275." (from `reports/metrics_test_day7.json`, test split)

## Thresholds (Precision/Recall)
* "For the High risk band, row-level precision is 61.0% and row-level recall is 67.2% in this synthetic setting." (from `reports/metrics_test_day7.json`, test split). *(Note: 61% precision means 39% of High alerts are false positives. Mention this trade-off if diving deep.)*
* "For the Medium risk band, row-level precision drops to 41.0% with recall on spike rows 91.4% in this synthetic setting." (from `reports/metrics_test_day7.json`, test split). *(Note: Row-level metrics from `reports/metrics_test_day7.json`; event-level recall from clinical utility reports was not saved in reports).*

## Forecast
* "Forecast RMSE at the 60-minute horizon is 18.41 mg/dL in this synthetic setting." (from `reports/metrics_forecast_val.json`, validation split)
* "The 80% coverage interval achieved 80.0% empirical coverage on the validation split used to calibrate the intervals; held-out forecast test metrics were not saved." (from `reports/metrics_forecast_val.json`, validation split)

## What-if Simulator
* "For the What-if Simulator test evaluation, the peak error is 1.0, 10.2 and 11.5 mg/dL for the three tested scenarios in this synthetic setting." (from `reports/WHATIF_TEST_DONE.json`, test split). *(Note: The uncertainty bands significantly under-cover).*

## Patient Moment
* "At 2026-01-03 21:50, Patient P007's glucose is 191.4 mg/dL. The risk band is High with a calibrated probability of 0.967, and the predicted peak is 302.3 mg/dL in this synthetic setting." (from bundled state `demo_bundle/states/P007_20260103_2150.json`, test patient moment)

## Realism Comparison
* "Time above 180 mg/dL (patient-level average) is 19.6% in the real cohort vs 68.6% in the synthetic cohort." (from `reports/realism_comparison.json` and `reports/real_range_check.json`, cohort comparison)
* "In the real dataset under the 39.5 to 500.5 mg/dL range in configs/real_data.yaml, 329 readings at the sensor lower limit (39.6 mg/dL, 2.2 mmol/L) are kept with a censored flag; 30 readings above 400 mg/dL (maximum 468) are kept (patient-level mean glucose 141.01 mg/dL, patient-level time below 70 of 0.0253, patient-level time above 180 of 19.6%)." (from `reports/real_range_check.json`, real data check)
