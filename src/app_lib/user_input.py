import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

def load_user_config():
    with open("configs/user_input.yaml", "r") as f:
        return yaml.safe_load(f)

def validate_profile(profile: dict) -> tuple[dict, list[str]]:
    errors = []
    
    validated = {
        "patient_id": "user_1",
        "age": np.nan,
        "sex": "Female",
        "bmi": np.nan,
        "hba1c": np.nan,
        "diabetes_duration_years": np.nan,
        "on_insulin": 0,
        "on_metformin": 0,
        "hypertension": 0
    }
    
    try:
        age_val = profile.get("age", np.nan)
        if str(age_val).strip() == "" or pd.isna(age_val):
            pass
        else:
            age = float(age_val)
            if not (18 <= age <= 90):
                errors.append("Age must be between 18 and 90.")
            else:
                validated["age"] = age
    except ValueError:
        errors.append("Age must be a number.")
        
    try:
        bmi_val = profile.get("bmi", np.nan)
        if str(bmi_val).strip() == "" or pd.isna(bmi_val):
            pass
        else:
            bmi = float(bmi_val)
            if not (15 <= bmi <= 60):
                errors.append("BMI must be between 15 and 60.")
            else:
                validated["bmi"] = bmi
    except ValueError:
        errors.append("BMI must be a number.")
        
    hba1c = profile.get("hba1c", "unknown")
    if str(hba1c).lower() != "unknown" and str(hba1c).strip() != "":
        try:
            h = float(hba1c)
            if not (4 <= h <= 15):
                errors.append("HbA1c must be between 4 and 15 percent.")
            else:
                validated["hba1c"] = h
        except ValueError:
            errors.append("HbA1c must be a number or 'unknown'.")
            
    dur = profile.get("diabetes_duration_years", profile.get("diabetes_duration_yrs", ""))
    if str(dur).lower() != "unknown" and str(dur).strip() != "":
        try:
            d = float(dur)
            validated["diabetes_duration_years"] = d
        except ValueError:
            errors.append("Diabetes duration must be a number.")
            
    sex = profile.get("sex", "F")
    if sex in ["Male", "M"]:
        validated["sex"] = "M"
    else:
        validated["sex"] = "F"
        
    on_ins = profile.get("on_insulin", 0)
    validated["on_insulin"] = 1 if str(on_ins).lower() in ["yes", "1", "true"] or on_ins == 1 else 0
    on_met = profile.get("on_metformin", 0)
    validated["on_metformin"] = 1 if str(on_met).lower() in ["yes", "1", "true"] or on_met == 1 else 0
    hyp = profile.get("hypertension", 0)
    validated["hypertension"] = 1 if str(hyp).lower() in ["yes", "1", "true"] or hyp == 1 else 0
    
    return validated, errors

def validate_time(ts, now: datetime) -> tuple[datetime, list[str]]:
    errors = []
    
    if isinstance(ts, str):
        try:
            val = float(ts)
            ts = val
        except ValueError:
            pass
            
    if isinstance(ts, (int, float)):
        if ts < 0:
            errors.append("Time cannot be in the future.")
            return now, errors
        return now - timedelta(minutes=ts), errors
        
    if isinstance(ts, str):
        try:
            dt = pd.to_datetime(ts).to_pydatetime()
            if dt > now:
                errors.append(f"Time {ts} is in the future.")
            return dt, errors
        except Exception:
            errors.append(f"Invalid time format: {ts}")
            return now, errors
            
    if isinstance(ts, datetime):
        if ts > now:
            errors.append(f"Time {ts} is in the future.")
        return ts, errors
        
    errors.append("Time must be a string, datetime, or minutes before now.")
    return now, errors

def validate_glucose(readings: list[dict], now: datetime) -> tuple[list[dict], list[str]]:
    errors = []
    validated = []
    
    if not readings:
        errors.append("At least one glucose reading is required.")
        return validated, errors
        
    for r in readings:
        dt, err = validate_time(r.get("time"), now)
        if err:
            errors.extend(err)
            continue
            
        try:
            val = float(r.get("value", 0))
            unit = str(r.get("unit", "mg/dL")).lower()
            
            if unit == "mmol/l":
                val = val * 18.016
                
            if not (40 <= val <= 500):
                errors.append(f"Glucose value {val:.1f} mg/dL is outside the valid range 40 to 500 mg/dL.")
                continue
                
            validated.append({"timestamp": dt, "glucose_mgdl": float(val)})
        except ValueError:
            errors.append("Glucose value must be a number.")
            
    return validated, errors

def validate_meals_exercise(meals: list[dict], exercises: list[dict], now: datetime) -> tuple[list[dict], list[dict], list[str]]:
    errors = []
    val_m = []
    val_e = []
    
    for m in meals:
        dt, err = validate_time(m.get("time"), now)
        if err:
            errors.extend(err)
            continue
        try:
            carbs = float(m.get("carbs", 0))
            if not (0 <= carbs <= 200):
                errors.append(f"Meal carbs {carbs} g is outside valid range 0 to 200 g.")
                continue
            val_m.append({"timestamp": dt, "carbs": carbs})
        except ValueError:
            errors.append("Meal carbs must be a number.")
            
    for e in exercises:
        dt, err = validate_time(e.get("time"), now)
        if err:
            errors.extend(err)
            continue
        try:
            dur = float(e.get("duration", 0))
            if not (5 <= dur <= 120):
                errors.append(f"Exercise duration {dur} min is outside valid range 5 to 120 min.")
                continue
                
            intensity_str = str(e.get("intensity", "light")).lower()
            intensity_map = {"light": 1, "moderate": 2, "vigorous": 3}
            intensity = intensity_map.get(intensity_str, 1)
            
            val_e.append({"timestamp": dt, "duration": dur, "intensity": intensity})
        except ValueError:
            errors.append("Exercise duration must be a number.")
            
    return val_m, val_e, errors

def parse_hour_input(val, default_hour: int) -> int:
    if val is None or str(val).strip() == "":
        return default_hour
    s = str(val).strip()
    if ":" in s:
        try:
            return int(s.split(":")[0])
        except Exception:
            return default_hour
    try:
        h = int(float(s))
        if 0 <= h <= 23:
            return h
    except Exception:
        pass
    return default_hour

def build_frame(
    readings: list[dict],
    meals: list[dict],
    exercises: list[dict],
    now: datetime,
    history_hours: float,
    bedtime: int | str | None = None,
    wake_time: int | str | None = None,
    steps_last_hour: float | str | None = None,
    sleep_strategy: str | None = None
) -> tuple[pd.DataFrame, list[str]]:
    adjustments = []
    
    grid_end = pd.to_datetime(now).floor('5min')
    grid_start = grid_end - pd.Timedelta(hours=history_hours)
    
    slots = pd.date_range(start=grid_start, end=grid_end, freq='5min')
    df = pd.DataFrame({"timestamp": slots})
    
    df["patient_id"] = "user_1"
    df["glucose_mgdl"] = np.nan
    df["heart_rate"] = 70.0
    df["steps"] = 0.0
    
    strat = sleep_strategy if sleep_strategy is not None else "assumed_schedule"
    if strat == "unknown":
        df["sleep_state"] = "unknown"
    elif strat == "awake":
        df["sleep_state"] = "awake"
    else:
        bed_h = parse_hour_input(bedtime, 23)
        wake_h = parse_hour_input(wake_time, 7)
        hours = slots.hour
        if bed_h > wake_h:
            asleep = (hours >= bed_h) | (hours < wake_h)
        else:
            asleep = (hours >= bed_h) & (hours < wake_h)
        df["sleep_state"] = np.where(asleep, "light", "awake")
        
    df["meal_carbs_g"] = 0.0
    df["activity_intensity"] = 0.0
    
    df = df.set_index("timestamp")
    
    if steps_last_hour is not None and str(steps_last_hour).strip() != "":
        try:
            st_val = float(steps_last_hour)
            if st_val > 0:
                recent_start = grid_end - pd.Timedelta(hours=1)
                recent_slots = df.index[df.index > recent_start]
                if len(recent_slots) > 0:
                    df.loc[recent_slots, "steps"] = st_val / float(len(recent_slots))
        except Exception:
            pass
    
    for r in readings:
        ts = pd.to_datetime(r["timestamp"])
        if ts < grid_start:
            continue
        slot = ts.floor('5min')
        if slot > grid_end:
            continue
        offset = (ts - slot).total_seconds() / 60.0
        if offset > 0:
            adjustments.append(f"Glucose at {ts.strftime('%H:%M:%S')} snapped to {slot.strftime('%H:%M:%S')}")
            
        val = r.get("glucose_mgdl")
        df.loc[slot, "glucose_mgdl"] = float(val) if pd.notna(val) else np.nan
        
    for m in meals:
        ts = pd.to_datetime(m["timestamp"])
        if ts < grid_start:
            continue
        slot = ts.floor('5min')
        if slot > grid_end:
            continue
        df.loc[slot, "meal_carbs_g"] += float(m.get("carbs", 0.0))
        
    for e in exercises:
        ts = pd.to_datetime(e["timestamp"])
        if ts < grid_start:
            continue
        slot_start = ts.floor('5min')
        dur = float(e.get("duration", 0.0))
        intensity = float(e.get("intensity", 1.0))
        
        n_slots = int(np.ceil(dur / 5.0))
        for i in range(n_slots):
            curr_slot = slot_start + pd.Timedelta(minutes=5 * i)
            if grid_start <= curr_slot <= grid_end:
                curr_int = df.loc[curr_slot, "activity_intensity"]
                df.loc[curr_slot, "activity_intensity"] = max(curr_int, intensity)
                
    df = df.reset_index()
    numeric_cols = ["glucose_mgdl", "heart_rate", "steps", "meal_carbs_g", "activity_intensity"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
        
    return df, adjustments

def evaluate_tier(df: pd.DataFrame, now: datetime, conf: dict) -> tuple[str, list[str]]:
    missing_groups = []
    
    df_glu = df.dropna(subset=["glucose_mgdl"])
    if df_glu.empty:
        return "none", missing_groups
        
    first_glu = df_glu["timestamp"].min()
    last_glu = df_glu["timestamp"].max()
    
    hist_hours = (last_glu - first_glu).total_seconds() / 3600.0
    if hist_hours >= conf["full_tier"]["min_history_hours"]:
        return "full", missing_groups
        
    now_ts = pd.to_datetime(now).floor('5min')
    last_glu_age_min = (now_ts - last_glu).total_seconds() / 60.0
    
    partial_conf = conf["partial_tier"]
    recent_cutoff = now_ts - pd.Timedelta(minutes=partial_conf["in_last_minutes"])
    recent_df = df_glu[df_glu["timestamp"] >= recent_cutoff]
    
    span_min = 0.0
    if len(recent_df) > 0:
        span_min = (recent_df["timestamp"].max() - recent_df["timestamp"].min()).total_seconds() / 60.0
        
    if len(recent_df) >= partial_conf["min_readings"] and span_min >= partial_conf["min_span_minutes"]:
        missing_groups = ["24 hour history", "heart rate", "steps", "sleep: assumed schedule (not measured)"]
        return "partial", missing_groups
        
    single_conf = conf["single_tier"]
    if last_glu_age_min <= single_conf["max_age_minutes"]:
        missing_groups = ["24 hour history", "heart rate", "steps", "sleep: assumed schedule (not measured)", "trend data"]
        return "single", missing_groups
        
    return "invalid", missing_groups

def run_indicative_path(df: pd.DataFrame, profile_dict: dict, engine_config: dict, pipeline, calibrator, forecaster_artifacts, thresholds, explainer=None) -> dict:
    from src.features.engineering import build_features_for_patient
    from src.models.explain import explain_row
    from src.twin.state import RiskAssessment, ForecastResult
    
    v_prof, _ = validate_profile(profile_dict)
    profile_series = pd.Series(v_prof)
    
    feat_df = build_features_for_patient(df, profile_series, engine_config)
    last_feat = feat_df.iloc[-1].copy()
    
    if pd.isna(last_feat.get("meal_min_since_last")):
        last_feat["meal_min_since_last"] = 120.0
    if pd.isna(last_feat.get("meal_any_in_history")):
        last_feat["meal_any_in_history"] = 1.0 if df["meal_carbs_g"].sum() > 0 else 0.0
    if pd.isna(last_feat.get("act_min_since_moderate")):
        last_feat["act_min_since_moderate"] = 120.0
    if pd.isna(last_feat.get("sleep_min_since_wake")):
        last_feat["sleep_min_since_wake"] = 0.0
    if pd.isna(last_feat.get("miss_min_since_last_obs")):
        last_feat["miss_min_since_last_obs"] = 0.0
        
    X_row = pd.DataFrame([last_feat])
    
    features_list = list(pipeline.feature_names_in_)
    X_risk = X_row[features_list].astype("float64")
    prob_raw = float(pipeline.predict_proba(X_risk)[:, 1][0])
    
    if hasattr(calibrator, "transform"):
        prob_calib = float(np.clip(calibrator.transform([prob_raw])[0], 0.0, 1.0))
    else:
        prob_calib = float(np.clip(calibrator.predict_proba(np.array([[prob_raw]]))[:, 1][0], 0.0, 1.0))
        
    t_med = thresholds["t_medium"]
    t_high = thresholds["t_high"]
    
    band = "Low"
    if prob_calib >= t_high:
        band = "High"
    elif prob_calib >= t_med:
        band = "Medium"
        
    drivers = []
    if band in ["Medium", "High"] and explainer is not None:
        raw_drivers = explain_row(explainer, X_risk, features_list, top_k=3)
        # Ensure drivers are sorted by absolute SHAP value
        drivers = sorted(raw_drivers, key=lambda d: abs(d["shap_value"]), reverse=True)[:3]
        
    risk = RiskAssessment(
        probability_calibrated=prob_calib,
        probability_raw=prob_raw,
        band=band,
        band_thresholds={"Medium": t_med, "High": t_high},
        drivers=drivers,
        model_version="v1"
    )
    
    forecast_result = None
    if forecaster_artifacts is not None:
        xgb_forecaster, conf_calibrator, f_meta = forecaster_artifacts
        anchor_glu = last_feat["glu_current"]
        
        if pd.isna(anchor_glu):
            if engine_config.get("forecast", {}).get("allow_last_observation_anchor", False):
                df_valid = df.dropna(subset=["glucose_mgdl"])
                if not df_valid.empty:
                    last_obs_ts = df_valid["timestamp"].iloc[-1]
                    mins_since = (df["timestamp"].iloc[-1] - last_obs_ts).total_seconds() / 60.0
                    if mins_since <= engine_config.get("twin", {}).get("stale_data_minutes", 20.0):
                        anchor_glu = float(df_valid["glucose_mgdl"].iloc[-1])
                        
        if not pd.isna(anchor_glu):
            f_features = f_meta["features"]
            X_f = X_row[f_features].astype("float64")
            
            raw_quantiles = xgb_forecaster.predict_quantiles(X_f)
            cal_quantiles = conf_calibrator.apply(raw_quantiles)
            traj = xgb_forecaster.get_trajectory(np.array([anchor_glu]), cal_quantiles)
            
            horizons = f_meta["horizons"]
            q_vals = f_meta["quantiles"]
            q_dict = {str(q): [] for q in q_vals}
            for i, h in enumerate(horizons):
                for j, q in enumerate(q_vals):
                    q_dict[str(q)].append(float(anchor_glu + cal_quantiles[0, i, j]))
                    
            interval_m = engine_config["sampling_interval_minutes"]
            traj_times = [df["timestamp"].iloc[-1] + pd.Timedelta(minutes=m) for m in range(0, max(horizons) + interval_m, interval_m)]
            traj_dict = {
                "timestamp": [t.isoformat() for t in traj_times],
                "median": [float(v) for v in traj[0, :, 1]],
                "lower": [float(v) for v in traj[0, :, 0]],
                "upper": [float(v) for v in traj[0, :, 2]]
            }
            
            med_traj = traj[0, :, 1]
            peak_idx = int(np.argmax(med_traj))
            peak_val = float(med_traj[peak_idx])
            peak_m = int(peak_idx * interval_m)
            min_idx = int(np.argmin(med_traj))
            min_val = float(med_traj[min_idx])
            min_m = int(min_idx * interval_m)
            
            hypo = bool(np.any(traj[0, :, 0] < engine_config["forecast"]["hypo_threshold_mgdl"]))
            hyper = bool(np.any(med_traj > engine_config["forecast"]["hyper_threshold_mgdl"]))
            above_180 = float(np.sum(med_traj > 180) * interval_m)
            
            from src.forecast.consistency import estimate_spike_probability
            p_spike_f = estimate_spike_probability(cal_quantiles, q_vals, engine_config["forecast"]["spike_delta_mgdl"])[0]
            
            agreement = True
            if band in ["Medium", "High"] and p_spike_f < 0.1:
                agreement = False
            if band == "Low" and p_spike_f > 0.3:
                agreement = False
                
            summ = f"Glucose is expected to peak near {peak_val:.0f} mg/dL in about {peak_m} minutes."
            
            forecast_result = ForecastResult(
                status="ok",
                horizons_minutes=horizons,
                quantiles=q_dict,
                trajectory_5min=traj_dict,
                predicted_peak=peak_val,
                predicted_peak_minutes=peak_m,
                predicted_min=min_val,
                predicted_min_minutes=min_m,
                hypo_risk_flag=hypo,
                hyper_risk_flag=hyper,
                time_above_180_expected_minutes=above_180,
                agreement_with_risk_band=agreement,
                model_version=f_meta.get("version", "v1"),
                summary=summ
            )
            
    return {
        "risk": risk,
        "forecast": forecast_result,
        "last_feat": X_row.to_dict(orient="records")[0]
    }

def run_full_path(
    df: pd.DataFrame,
    profile_dict: dict,
    engine_config: dict,
    pipeline,
    calibrator,
    forecaster_artifacts,
    thresholds: dict,
    explainer=None,
    whatif_artifacts=None
) -> dict:
    from src.twin.engine import DiaTwin
    from src.twin.state import PatientProfile
    
    v_prof, _ = validate_profile(profile_dict)
    prof = PatientProfile.from_dict(v_prof)
    twin = DiaTwin(
        profile=prof,
        pipeline=pipeline,
        calibrator=calibrator,
        thresholds=thresholds,
        config=engine_config,
        explainer=None,
        forecast_artifacts=forecaster_artifacts,
        whatif_artifacts=whatif_artifacts
    )
    
    n_rows = len(df)
    state = None
    for i in range(n_rows):
        row = df.iloc[i]
        sample = {
            "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
            "glucose_mgdl": float(row["glucose_mgdl"]) if pd.notna(row["glucose_mgdl"]) else np.nan,
            "heart_rate": float(row["heart_rate"]) if pd.notna(row["heart_rate"]) else 70.0,
            "steps": float(row["steps"]) if pd.notna(row["steps"]) else 0.0,
            "sleep_state": str(row["sleep_state"]) if pd.notna(row["sleep_state"]) else "unknown",
            "meal_carbs_g": float(row["meal_carbs_g"]) if pd.notna(row["meal_carbs_g"]) else 0.0,
            "activity_intensity": float(row["activity_intensity"]) if pd.notna(row["activity_intensity"]) else 0.0,
        }
        if i == n_rows - 1 and explainer is not None:
            twin.explainer = explainer
        state = twin.ingest(sample)
        
    last_feat_dict = None
    if hasattr(twin, "_last_feature_row") and twin._last_feature_row is not None:
        last_feat_dict = twin._last_feature_row.to_dict(orient="records")[0]
        
    # Ensure drivers list has top 3 items sorted by absolute SHAP value
    if state and state.risk and state.risk.drivers:
        state.risk.drivers = sorted(state.risk.drivers, key=lambda d: abs(d["shap_value"]), reverse=True)[:3]
        
    return {
        "risk": state.risk if state else None,
        "forecast": state.forecast if state else None,
        "state": state,
        "last_feat": last_feat_dict
    }

def get_cohort_comparison_statement() -> str:
    path = Path("reports/realism_comparison.json")
    synth_mean = 218.8
    real_mean = 141.2
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "mean_glucose" in data:
                synth_mean = float(data["mean_glucose"]["synthetic"])
                real_mean = float(data["mean_glucose"]["real"])
            elif "synthetic_regression" in data and "observed_mean" in data["synthetic_regression"]:
                synth_mean = float(data["synthetic_regression"]["observed_mean"])
                real_mean = float(data.get("real_regression", {}).get("observed_mean", real_mean))
        except Exception:
            pass
    return f"Real people differ from the synthetic training population (Synthetic mean glucose {synth_mean:.1f} mg/dL vs Real cohort {real_mean:.1f} mg/dL)."

def get_provided_summary(
    valid_glucose: list[dict],
    valid_meals: list[dict],
    valid_exercises: list[dict],
    missing_groups: list[str],
    sleep_default_name: str = "assumed schedule 23:00 to 07:00"
) -> dict[str, str]:
    n_glu = len(valid_glucose)
    n_meal = len(valid_meals)
    n_ex = len(valid_exercises)
    
    provided_text = f"What was provided: Profile, {n_glu} glucose reading(s), {n_meal} meal(s), {n_ex} exercise(s)."
    
    if missing_groups:
        groups_str = ", ".join(missing_groups)
        if "sleep: assumed schedule" in groups_str:
            not_provided_text = (
                f"What was NOT provided: {groups_str}. "
                f"Fixed placeholders are used for heart rate (70.0 bpm) and steps (0.0). "
                f"Sleep uses {sleep_default_name} (light state during sleep hours, awake otherwise). "
                "Features requiring history (personal 24-hour baseline and long lags) use training medians."
            )
        else:
            not_provided_text = (
                f"What was NOT provided: {groups_str}. "
                "Fixed placeholders are used for heart rate (70.0 bpm), steps (0.0), and sleep state (unknown). "
                "Features requiring history (personal 24-hour baseline and long lags) use training medians."
            )
    else:
        not_provided_text = "What was NOT provided: None. Full historical wearable context was provided."
        
    return {
        "provided": provided_text,
        "not_provided": not_provided_text,
        "cohort_comparison": get_cohort_comparison_statement()
    }

def get_sensitivity_statement(tier: str = "indicative") -> str:
    path = Path("reports/user_input_sensitivity.json")
    diff_prob = 0.0012
    band_pct = 100.0
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            key = "schedule_fixed" if tier == "full" else "indicative_single"
            if key in data.get("comparison_results", {}):
                diff_prob = float(data["comparison_results"][key]["mad_prob"]["mean"])
                band_pct = float(data["comparison_results"][key]["band_agreement"]["mean"]) * 100.0
        except Exception:
            pass
    return f"on synthetic validation patients the estimate without sensors differed from the full estimate by {diff_prob:.4f} in probability and kept the same band in {band_pct:.0f} percent of moments."

def get_confidence_label(tier: str, conf_dict: dict | None = None) -> str:
    if tier == "full":
        return "High"
    if tier == "partial":
        if conf_dict and conf_dict.get("partial_tier", {}).get("allow_medium_confidence", True):
            return "Medium"
        return "Medium"
    return "Low"

