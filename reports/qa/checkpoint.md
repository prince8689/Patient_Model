# QA Checkpoint

| Item | Status | Evidence |
| :--- | :--- | :--- |
| 1. Repository State | PASS | `git log --oneline -8; git status --short` output shows 8 commits and several modified/untracked files. |
| 2. Protected Files | PASS | `Python 3.13.15` and `Protected files count: 16`. |
| 3. README numbers | FAIL | `reports/metrics_forecast_val.json` has `18.41` for 60m RMSE, while README matches this but the demo script has `14.5`. |
| 4. Git Attributes | FAIL | `git ls-files --eol` shows CRLF in index (`i/crlf w/crlf`) for `FROZEN.json` and others, though `config.yaml` is `i/lf w/lf`. |
| 5. Clone SHA256 | FAIL | `configs/config.yaml` mismatches. Expected `8329f...` Actual `a39e...`. |
| 6. Demo bundle test | FAIL | `demo_preflight.py` crashed with `ModuleNotFoundError: No module named 'yaml'` because `requirements-demo.txt` lacks pyyaml. |
| 7. Config audit | PASS | `audit_config()` returns `"unverified: config not verified in this checkout"` when the commit is not found. |
| 8. QA_REPORT.md | FAIL | The section "Fresh-Clone Portability Check" says "**Result**: **PASS**" even though the clone test fails. |
| 9. Bundle outputs | PASS | Script output: `No differences found.` `Max absolute diff: 0.0`. |
| 10. Run sheet values | PASS | Run sheet states "High risk band", "rising after a recent meal". State file P007: Glucose 191.4, Band High, Prob 0.967, Drivers `['meal_min_since_last', 'meal_cob_estimate', 'ehr_hba1c']`, Predicted Peak 302.3. |
| 11. numbers_for_video | FAIL | Lines 16, 17, 20 contain numbers not present in `reports/` (14.5 mg/dL RMSE, 81.2% coverage, 92.4% accuracy). P040 is not mentioned. |
| 12. Main folder pytest| PASS | Output: `68 passed, 4 warnings in 654.75s`. No skipped tests. |
| 13. Clone pytest | FAIL | Output: `2 failed, 58 passed, 4 warnings, 8 errors` (due to missing files like `splits.csv` and `xgb_v1.joblib`). Test bodies were modified to skip missing artifacts: e.g. `if not sample_patient: pytest.skip("No test patients")` in `test_twin.py` and `if not state_files: pytest.skip(f"No state files for {pid}")` in `test_app_lib.py`. |

## Still to do
- [FAIL] 3. README results table
- [FAIL] 4. Git Attributes
- [FAIL] 5. Clone SHA256
- [FAIL] 6. Demo bundle test
- [FAIL] 8. QA_REPORT.md
- [FAIL] 11. numbers_for_video
- [FAIL] 13. Clone pytest
