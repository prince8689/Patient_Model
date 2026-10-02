# Demo Numbers for Video Script

When quoting metrics in the video, use the following exact numbers and intervals. 

**Mandatory Phrasing**: You must preface or append quotes with: *"in this synthetic setting"*.

## Risk Model Classification
* "In this synthetic setting, the model achieved a ROC AUC of 0.925 (95% CI: 0.907 - 0.944)."
* "Calibration Error (ECE) is very low at 0.027 (95% CI: 0.012 - 0.057)."

## Thresholds (Precision/Recall)
* "For the High risk band, precision is 61.0% and recall is 67.2% in this synthetic setting." *(Note: 61% precision means 39% of High alerts are false positives. Mention this trade-off if diving deep.)*
* "For the Medium risk band, precision drops to 41.0% but captures 91.4% of events (recall)." *(Note: Weak precision, very wide capture net).*

## Forecast
* "Forecast RMSE at the 60-minute horizon is 14.5 mg/dL (95% CI: 13.2 - 15.8) in this synthetic setting." (n=2150)
* "The 80% coverage interval achieved 81.2% empirical coverage (95% CI: 79.5 - 82.9)."

## What-if Simulator
* "What-if directional accuracy reached 92.4% in this synthetic setting." (n=120)

*(Note: Forecast and What-if metrics are static baseline results as evaluated on the test set prior to model freeze.)*
