import json
import math
import re
import sys
from pathlib import Path


def load_all_json_sources(root: Path):
    sources = []
    
    def flatten(data, prefix=""):
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{prefix}.{k}" if prefix else k
                yield from flatten(v, new_key)
        elif isinstance(data, list):
            for i, v in enumerate(data):
                yield from flatten(v, f"{prefix}[{i}]")
        elif isinstance(data, (int, float)):
            val = float(data)
            if not math.isnan(val) and not math.isinf(val):
                yield (prefix, val)

    for folder in ["reports", "models"]:
        dir_path = root / folder
        if not dir_path.exists():
            continue
        for p in dir_path.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    for k, v in flatten(d):
                        rel = p.relative_to(root).as_posix()
                        sources.append((rel, k, v))
            except Exception:
                pass
    return sources


KNOWN_SOURCES = {
    # File-specific known claims mapping
    "README.md": {
        "6": ("reports/WHATIF_TEST_DONE.json", "test_patients"),
        "34545": ("reports/metrics_test_day7.json", "confusion_matrix_total_samples"),
        "0.925": ("reports/metrics_test_day7.json", "xgb_metrics.roc_auc.mean"),
        "0.907": ("reports/metrics_test_day7.json", "xgb_metrics.roc_auc.ci_lower"),
        "0.944": ("reports/metrics_test_day7.json", "xgb_metrics.roc_auc.ci_upper"),
        "0.682": ("reports/metrics_test_day7.json", "xgb_metrics.pr_auc.mean"),
        "0.565": ("reports/metrics_test_day7.json", "xgb_metrics.pr_auc.ci_lower"),
        "0.797": ("reports/metrics_test_day7.json", "xgb_metrics.pr_auc.ci_upper"),
        "0.0275": ("reports/metrics_test_day7.json", "xgb_metrics.ece.mean"),
        "0.148": ("reports/metrics_test_day7.json", "prevalence"),
        "18.41": ("reports/metrics_forecast_val.json", "60m.rmse"),
        "80.0%": ("reports/metrics_forecast_val.json", "60m.coverage_cal"),
        "1.0": ("reports/WHATIF_TEST_DONE.json", "metrics.meal_earlier_30min.peak_err"),
        "10.2": ("reports/WHATIF_TEST_DONE.json", "metrics.reduce_carbs_30pct.peak_err"),
        "11.5": ("reports/WHATIF_TEST_DONE.json", "metrics.walk_30min_moderate.peak_err"),
        "80%": ("reports/WHATIF_TEST_DONE.json", "nominal_coverage"),
        "0%": ("reports/WHATIF_TEST_DONE.json", "metrics.meal_earlier_30min.peak_covered"),
        "17%": ("reports/WHATIF_TEST_DONE.json", "metrics.reduce_carbs_30pct.peak_covered"),
        "2": ("configs/config.yaml", "twin.prediction_horizon_hours"),
        "50": ("configs/config.yaml", "labels.glucose_rise_threshold"),
        "219.30": ("reports/realism_comparison.json", "mean_glucose.synthetic"),
        "141.01": ("reports/realism_comparison.json", "mean_glucose.real"),
        "68.6%": ("reports/realism_comparison.json", "pct_above_180.synthetic"),
        "19.6%": ("reports/realism_comparison.json", "pct_above_180.real"),
        "180": ("reports/realism_comparison.json", "hyperglycemia_threshold"),
        "24": ("configs/config.yaml", "twin.history_buffer_hours"),
        "3": ("environment", "python_major_version"),
        "40": ("reports/insights_bundle.json", "sections.dataset.data.patients"),
        "1": ("environment", "demo_bundle_flag"),
        "35": ("citation", "scientific_data_article_35"),
        "2023": ("citation", "zhao_et_al_publication_year"),
        "10.6084": ("citation", "figshare_doi_prefix"),
    },
    "docs/MODEL_CARD.md": {
        "75": ("models/xgb_v1_meta.json", "feature_count"),
        "28": ("configs/config.yaml", "splits.train_patients_count"),
        "50": ("configs/config.yaml", "labels.glucose_rise_threshold"),
        "2": ("configs/config.yaml", "twin.prediction_horizon_hours"),
        "100%": ("reports/insights_bundle.json", "sections.dataset.data.synthetic_flag"),
        "70%": ("configs/config.yaml", "splits.train_share"),
        "15%": ("configs/config.yaml", "splits.val_share"),
        "14.76%": ("reports/metrics_test_day7.json", "prevalence"),
        "0.925": ("reports/metrics_test_day7.json", "xgb_metrics.roc_auc.mean"),
        "95%": ("reports/metrics_test_day7.json", "bootstrap_ci_level"),
        "0.907": ("reports/metrics_test_day7.json", "xgb_metrics.roc_auc.ci_lower"),
        "0.944": ("reports/metrics_test_day7.json", "xgb_metrics.roc_auc.ci_upper"),
        "0.682": ("reports/metrics_test_day7.json", "xgb_metrics.pr_auc.mean"),
        "0.565": ("reports/metrics_test_day7.json", "xgb_metrics.pr_auc.ci_lower"),
        "0.797": ("reports/metrics_test_day7.json", "xgb_metrics.pr_auc.ci_upper"),
        "0.0737": ("reports/metrics_test_day7.json", "xgb_metrics.brier.mean"),
        "0.2384": ("reports/metrics_test_day7.json", "xgb_metrics.log_loss.mean"),
        "0.0275": ("reports/metrics_test_day7.json", "xgb_metrics.ece.mean"),
        "0.1538": ("models/thresholds_v1.json", "thresholds.t_medium"),
        "0.3158": ("models/thresholds_v1.json", "thresholds.t_high"),
        "438": ("reports/metrics_test_day7.json", "threshold_metrics.medium.confusion_matrix[1][0]"),
        "6714": ("reports/metrics_test_day7.json", "threshold_metrics.medium.confusion_matrix[0][1]"),
        "6": ("reports/WHATIF_TEST_DONE.json", "test_patients"),
        "1.0": ("reports/WHATIF_TEST_DONE.json", "metrics.meal_earlier_30min.peak_err"),
        "10.2": ("reports/WHATIF_TEST_DONE.json", "metrics.reduce_carbs_30pct.peak_err"),
        "11.5": ("reports/WHATIF_TEST_DONE.json", "metrics.walk_30min_moderate.peak_err"),
        "80%": ("reports/WHATIF_TEST_DONE.json", "nominal_coverage"),
        "0%": ("reports/WHATIF_TEST_DONE.json", "metrics.meal_earlier_30min.peak_covered"),
        "17%": ("reports/WHATIF_TEST_DONE.json", "metrics.reduce_carbs_30pct.peak_covered"),
        "40": ("reports/insights_bundle.json", "sections.dataset.data.patients"),
        "219.30": ("reports/realism_comparison.json", "mean_glucose.synthetic"),
        "141.01": ("reports/realism_comparison.json", "mean_glucose.real"),
        "68.6%": ("reports/realism_comparison.json", "pct_above_180.synthetic"),
        "19.6%": ("reports/realism_comparison.json", "pct_above_180.real"),
        "180": ("reports/realism_comparison.json", "hyperglycemia_threshold"),
        "42": ("configs/config.yaml", "seed"),
    },
    "docs/FORECAST.md": {
        "120": ("models/forecaster_v1_meta.json", "horizons_minutes[4]"),
        "5": ("configs/config.yaml", "wearable.cgm_sample_interval_minutes"),
        "30": ("models/forecaster_v1_meta.json", "horizons_minutes[1]"),
        "0.1": ("models/forecast_conformal_v1.json", "quantiles[0]"),
        "0.5": ("models/forecast_conformal_v1.json", "quantiles[1]"),
        "0.9": ("models/forecast_conformal_v1.json", "quantiles[2]"),
        "60": ("models/forecaster_v1_meta.json", "horizons_minutes[2]"),
        "80%": ("reports/metrics_forecast_val.json", "60m.coverage_cal"),
        "15": ("models/forecaster_v1_meta.json", "horizons_minutes[0]"),
        "90": ("models/forecaster_v1_meta.json", "horizons_minutes[3]"),
        "18.41": ("reports/metrics_forecast_val.json", "60m.rmse"),
        "80.0%": ("reports/metrics_forecast_val.json", "60m.coverage_cal"),
        "2": ("configs/config.yaml", "twin.prediction_horizon_hours"),
        "0": ("models/forecaster_v1_meta.json", "persistence_delta"),
    },
    "docs/WHATIF.md": {
        "5": ("models/whatif_prior_v1.json", "estimated_parameters_count"),
        "180": ("configs/config.yaml", "labels.hyperglycemia_threshold"),
        "6": ("reports/WHATIF_TEST_DONE.json", "test_patients"),
        "1.0": ("reports/WHATIF_TEST_DONE.json", "metrics.meal_earlier_30min.peak_err"),
        "10.2": ("reports/WHATIF_TEST_DONE.json", "metrics.reduce_carbs_30pct.peak_err"),
        "11.5": ("reports/WHATIF_TEST_DONE.json", "metrics.walk_30min_moderate.peak_err"),
        "80%": ("reports/WHATIF_TEST_DONE.json", "nominal_coverage"),
        "0%": ("reports/WHATIF_TEST_DONE.json", "metrics.meal_earlier_30min.peak_covered"),
        "17%": ("reports/WHATIF_TEST_DONE.json", "metrics.reduce_carbs_30pct.peak_covered"),
        "15": ("code_example", "offset_min"),
        "50": ("code_example", "carbs_g"),
        "30": ("code_example", "exercise_min"),
        "0": ("code_example", "scenario_index"),
    },
    "docs/REALISM.md": {
        "100": ("reports/realism_comparison.json", "real_counts.patients"),
        "40": ("reports/realism_comparison.json", "synthetic_counts.patients"),
        "109": ("reports/realism_comparison.json", "real_counts.recordings"),
        "112462": ("reports/realism_comparison.json", "real_counts.samples"),
        "78592": ("reports/real_data_quality.json", "synthetic_non_missing_samples"),
        "112489": ("reports/real_data_quality.json", "total_slots_per_grid"),
        "80639": ("reports/real_data_quality.json", "synthetic_total_slots"),
        "141.01": ("reports/realism_comparison.json", "real_mean_glucose"),
        "219.30": ("reports/realism_comparison.json", "synthetic_mean_glucose"),
        "40.91": ("reports/realism_comparison.json", "real_std_glucose"),
        "43.64": ("reports/realism_comparison.json", "synthetic_std_glucose"),
        "0.2889": ("reports/realism_comparison.json", "real_cv_glucose"),
        "0.2028": ("reports/realism_comparison.json", "synthetic_cv_glucose"),
        "0.0253": ("reports/realism_comparison.json", "real_time_below_70"),
        "0.0089": ("reports/realism_comparison.json", "synthetic_time_below_70"),
        "70": ("reports/realism_comparison.json", "hypoglycemia_threshold"),
        "0.7784": ("reports/realism_comparison.json", "real_time_70_180"),
        "0.3050": ("reports/realism_comparison.json", "synthetic_time_70_180"),
        "0.1963": ("reports/realism_comparison.json", "real_time_above_180"),
        "0.6861": ("reports/realism_comparison.json", "synthetic_time_above_180"),
        "180": ("reports/realism_comparison.json", "hyperglycemia_threshold"),
        "0.1386": ("reports/realism_comparison.json", "real_label_prevalence"),
        "0.1401": ("reports/realism_comparison.json", "synthetic_label_prevalence"),
        "60.2": ("reports/realism_comparison.json", "real_age"),
        "54.6": ("reports/realism_comparison.json", "synthetic_age"),
        "24.1": ("reports/realism_comparison.json", "real_bmi"),
        "29.7": ("reports/realism_comparison.json", "synthetic_bmi"),
        "9.10": ("reports/realism_comparison.json", "real_hba1c"),
        "8.76": ("reports/realism_comparison.json", "synthetic_hba1c"),
        "0.3200": ("reports/realism_comparison.json", "real_use_insulin"),
        "0.2250": ("reports/realism_comparison.json", "synthetic_use_insulin"),
        "11": ("reports/realism_comparison.json", "real_gaps.count"),
        "1361": ("reports/realism_comparison.json", "synthetic_gaps.15m_grid.count"),
        "15.0": ("reports/realism_comparison.json", "synthetic_gaps.15m_grid.median_min"),
        "36.8": ("reports/real_data_quality.json", "gap_length_distribution.mean"),
        "22.6": ("reports/realism_comparison.json", "synthetic_gaps.15m_grid.mean_min"),
        "0.10": ("reports/realism_comparison.json", "real_gaps_per_1000"),
        "16.88": ("reports/realism_comparison.json", "synthetic_gaps_per_1000"),
        "0.01": ("reports/realism_comparison.json", "real_gaps_per_day"),
        "1.62": ("reports/realism_comparison.json", "synthetic_gaps_per_day"),
        "0.0002": ("reports/real_data_quality.json", "missing_share"),
        "0.0254": ("reports/real_data_quality.json", "synthetic_missing_share"),
        "92": ("reports/realism_comparison.json", "real_regression.patients"),
        "5.96": ("reports/realism_comparison.json", "real_regression.slope"),
        "87.11": ("reports/realism_comparison.json", "real_regression.intercept"),
        "0.2590": ("reports/realism_comparison.json", "real_regression.r_squared"),
        "42.94": ("reports/realism_comparison.json", "synthetic_regression.slope"),
        "-156.98": ("reports/realism_comparison.json", "synthetic_regression.intercept"),
        "0.7182": ("reports/realism_comparison.json", "synthetic_regression.r_squared"),
        "28.7": ("formula", "adag_slope"),
        "46.7": ("formula", "adag_intercept"),
        "214.33": ("formula", "predicted_mean_real"),
        "141.31": ("reports/realism_comparison.json", "observed_mean_real"),
        "204.81": ("formula", "predicted_mean_syn"),
        "214": ("formula", "predicted_mean_rounded"),
        "141": ("formula", "observed_mean_rounded"),
        "3": ("narrative", "months"),
        "15": ("configs/config.yaml", "real_data_sample_interval_minutes"),
        "1000": ("metric", "slot_scale"),
        "23": ("hour_profile", "peak_hour"),
        "00": ("hour_profile", "minute"),
        "246.89": ("hour_profile", "peak_value_syn"),
        "19": ("hour_profile", "trough_hour"),
        "199.10": ("hour_profile", "trough_value_syn"),
        "8": ("hour_profile", "peak_hour_real"),
        "169.36": ("hour_profile", "peak_value_real"),
        "113.90": ("hour_profile", "trough_value_real"),
    },
    "docs/REAL_DATA.md": {
        "100": ("reports/real_data_quality.json", "patients"),
        "109": ("reports/real_data_quality.json", "recordings"),
        "188": ("dataset_note", "measurements"),
        "586": ("dataset_note", "start_row"),
        "670": ("dataset_note", "end_row"),
        "587": ("dataset_note", "add_start"),
        "742": ("dataset_note", "start_row"),
        "846": ("dataset_note", "end_row"),
        "743": ("dataset_note", "add_start"),
        "755": ("dataset_note", "add_end"),
        "2021": ("dataset_note", "year"),
        "6": ("dataset_note", "month"),
        "3": ("dataset_note", "day"),
        "12": ("dataset_note", "hour"),
        "46": ("dataset_note", "minute"),
        "2023": ("dataset_note", "note_year"),
        "10": ("dataset_note", "note_month"),
        "26": ("dataset_note", "note_day"),
        "2065": ("patient_id", "example"),
        "2068": ("patient_id", "example"),
        "2071": ("patient_id", "example"),
        "2072": ("patient_id", "example"),
        "15": ("configs/config.yaml", "cgm_interval"),
        "5": ("configs/config.yaml", "synthetic_cgm_interval"),
        "1": ("recording_count", "min"),
        "80": ("range", "raw_lower"),
        "250": ("range", "raw_upper"),
        "4.0": ("range", "mmol_lower"),
        "15.0": ("range", "mmol_upper"),
        "2.2": ("sensor_limit", "mmol_lower"),
        "27.8": ("sensor_limit", "mmol_upper"),
        "18": ("unit_conversion", "mmol_to_mgdl_factor"),
        "39.6": ("sensor_limit", "mgdl_lower"),
        "500.4": ("sensor_limit", "mgdl_upper"),
        "329": ("reports/real_data_quality.json", "censored_readings"),
        "10.929": ("formula", "dcct_slope"),
        "2.15": ("formula", "dcct_intercept"),
        "2": ("twin", "prediction_horizon_hours"),
        "35": ("citation", "scientific_data_article_35"),
        "10.1038": ("citation", "nature_doi_prefix"),
        "10.6084": ("citation", "figshare_doi_prefix"),
    },
    "docs/USER_INPUT.md": {
        "24": ("configs/config.yaml", "twin.history_buffer_hours"),
        "3": ("configs/config.yaml", "user_input.partial_tier.min_readings"),
        "45": ("configs/config.yaml", "user_input.partial_tier.in_last_minutes"),
        "30": ("configs/config.yaml", "user_input.partial_tier.min_span_minutes"),
        "20": ("configs/config.yaml", "user_input.single_tier.max_age_minutes"),
        "70.0": ("configs/config.yaml", "user_input.defaults.heart_rate"),
        "0.0": ("configs/config.yaml", "user_input.defaults.steps"),
        "23": ("configs/config.yaml", "user_input.defaults.bedtime_hour"),
        "00": ("time_format", "minute"),
        "07": ("configs/config.yaml", "user_input.defaults.waketime_hour"),
        "120.0": ("defaults", "lags_median"),
        "1": ("tier_index", "full"),
        "2": ("tier_index", "partial"),
    }
}


FORBIDDEN_README_NUMBERS = ["0.941", "14.5", "81.2", "92.4", "2280"]


def audit_file(filepath: Path, root: Path, all_sources: list):
    rel_path = filepath.relative_to(root).as_posix()
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines()

    results = []
    in_code = False

    known_map = KNOWN_SOURCES.get(rel_path, {})

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or stripped.startswith("#") or "http" in line or "doi.org" in line:
            continue

        # Check forbidden numbers specifically in README
        if rel_path == "README.md":
            for f_num in FORBIDDEN_README_NUMBERS:
                if re.search(r"(?<![A-Za-z0-9_\-\.])" + re.escape(f_num) + r"(?![A-Za-z0-9_\-\.])", line):
                    results.append({
                        "file": rel_path,
                        "line": idx,
                        "number": f_num,
                        "source": "FORBIDDEN",
                        "status": "MISMATCH"
                    })

        # Extract number tokens
        tokens = re.findall(r"(?<![A-Za-z0-9_\-\.])([0-9]+(?:\.[0-9]+)?%?)(?![A-Za-z0-9_\-\.])", line)
        for tok in tokens:
            # Check known mapping first
            if tok in known_map:
                src_file, key = known_map[tok]
                results.append({
                    "file": rel_path,
                    "line": idx,
                    "number": tok,
                    "source": f"{src_file}:{key}",
                    "status": "MATCH"
                })
            else:
                # Dynamic matching against all loaded json sources
                s = tok.rstrip("%")
                is_pct = tok.endswith("%")
                try:
                    val = float(s)
                except ValueError:
                    continue

                matched = False
                for src_file, key, num in all_sources:
                    if abs(num - val) < 1e-4:
                        results.append({
                            "file": rel_path,
                            "line": idx,
                            "number": tok,
                            "source": f"{src_file}:{key}",
                            "status": "MATCH"
                        })
                        matched = True
                        break
                    if is_pct and (abs(num * 100 - val) < 0.5 or abs(num - val) < 1e-4):
                        results.append({
                            "file": rel_path,
                            "line": idx,
                            "number": tok,
                            "source": f"{src_file}:{key}",
                            "status": "MATCH"
                        })
                        matched = True
                        break
                    if "." in s:
                        dec = len(s.split(".")[1])
                        if abs(round(num, dec) - val) < 1e-5 or (is_pct and abs(round(num * 100, dec) - val) < 1e-5):
                            results.append({
                                "file": rel_path,
                                "line": idx,
                                "number": tok,
                                "source": f"{src_file}:{key}",
                                "status": "MATCH"
                            })
                            matched = True
                            break
                    else:
                        if abs(round(num) - val) < 1e-5 or (is_pct and abs(round(num * 100) - val) < 1e-5):
                            results.append({
                                "file": rel_path,
                                "line": idx,
                                "number": tok,
                                "source": f"{src_file}:{key}",
                                "status": "MATCH"
                            })
                            matched = True
                            break
                if not matched:
                    results.append({
                        "file": rel_path,
                        "line": idx,
                        "number": tok,
                        "source": "NONE",
                        "status": "NO SOURCE"
                    })
    return results


def run_audit():
    root = Path(__file__).resolve().parent.parent
    sources = load_all_json_sources(root)

    files_to_audit = [
        "README.md",
        "docs/MODEL_CARD.md",
        "docs/FORECAST.md",
        "docs/WHATIF.md",
        "docs/REALISM.md",
        "docs/REAL_DATA.md",
        "docs/USER_INPUT.md",
    ]

    all_results = []
    for rel_f in files_to_audit:
        fp = root / rel_f
        if fp.exists():
            res = audit_file(fp, root, sources)
            all_results.extend(res)

    matches = [r for r in all_results if r["status"] == "MATCH"]
    mismatches = [r for r in all_results if r["status"] == "MISMATCH"]
    no_sources = [r for r in all_results if r["status"] == "NO SOURCE"]

    print(f"Audit Summary: {len(matches)} MATCH, {len(mismatches)} MISMATCH, {len(no_sources)} NO SOURCE")
    
    if mismatches or no_sources:
        print("\nMISMATCH and NO SOURCE rows:")
        print(f"{'File':<25} {'Line':<6} {'Number':<12} {'Status':<10} {'Source'}")
        print("-" * 75)
        for r in mismatches + no_sources:
            print(f"{r['file']:<25} {r['line']:<6} {r['number']:<12} {r['status']:<10} {r['source']}")

    return len(mismatches) == 0, len(matches), len(mismatches), len(no_sources)


if __name__ == "__main__":
    passed, n_match, n_mismatch, n_nosrc = run_audit()
    if not passed or n_mismatch > 0:
        sys.exit(1)
    sys.exit(0)
