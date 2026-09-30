import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from .state import (
    PatientProfile, Measurement, RiskAssessment, DataQuality, 
    AlertEvent, TwinState, GlucoseSummary, TwinContext
)
from src.features.engineering import build_features_for_patient
from src.models.explain import explain_row

logger = logging.getLogger(__name__)

class DiaTwin:
    def __init__(self, profile: PatientProfile, pipeline, calibrator, thresholds: dict, config: dict, explainer=None):
        self.profile = profile
        self.pipeline = pipeline
        self.calibrator = calibrator
        self.thresholds = thresholds
        self.config = config
        self.explainer = explainer
        
        self.interval_m = config["sampling_interval_minutes"]
        self.history_buffer_m = config["twin"]["history_buffer_hours"] * 60
        self.warmup_m = config["twin"]["warmup_hours"] * 60
        
        # Buffer
        self.buffer: List[Dict[str, Any]] = []
        self.last_timestamp: Optional[pd.Timestamp] = None
        
        # Cumulative state
        self.last_meal_ts: Optional[pd.Timestamp] = None
        self.last_meal_carbs: float = 0.0
        self.last_act_ts: Optional[pd.Timestamp] = None
        self.last_wake_ts: Optional[pd.Timestamp] = None
        self.last_obs_ts: Optional[pd.Timestamp] = None
        
        # History
        self.alert_history: List[AlertEvent] = []
        self.risk_history: List[Dict[str, Any]] = []
        
        # Precompute profile series for feature building
        self.profile_series = pd.Series(self.profile.to_dict())

    def _validate_sample(self, sample: dict) -> dict:
        forbidden = ["label", "spike_next_2h", "sim_params", "archetype", "baseline_insulin_sensitivity"]
        for k in forbidden:
            if k in sample:
                raise ValueError(f"Forbidden column in stream: {k}")
                
        # Fill missing keys with defaults
        validated = {
            "timestamp": pd.to_datetime(sample["timestamp"]),
            "glucose_mgdl": sample.get("glucose_mgdl"),
            "heart_rate": sample.get("heart_rate", 70.0),
            "steps": sample.get("steps", 0.0),
            "sleep_state": sample.get("sleep_state", "awake"),
            "meal_carbs_g": sample.get("meal_carbs_g", 0.0),
            "activity_intensity": sample.get("activity_intensity", 0.0),
            "patient_id": self.profile.patient_id
        }
        
        # Range checks
        g = validated["glucose_mgdl"]
        if g is not None:
            if g < self.config["glucose_min"] or g > self.config["glucose_max"]:
                validated["glucose_mgdl"] = np.nan
                
        return validated

    def _update_cumulative_state(self, row: dict):
        ts = row["timestamp"]
        if row["meal_carbs_g"] > 0:
            self.last_meal_ts = ts
            self.last_meal_carbs = row["meal_carbs_g"]
        if row["activity_intensity"] >= 2:
            self.last_act_ts = ts
        if row["sleep_state"] == "awake":
            # wake transition logic: if the previous state was not awake
            if len(self.buffer) >= 2 and self.buffer[-2]["sleep_state"] != "awake":
                self.last_wake_ts = ts
        if not pd.isna(row["glucose_mgdl"]):
            self.last_obs_ts = ts

    def ingest(self, sample: dict) -> TwinState:
        try:
            row = self._validate_sample(sample)
        except Exception as e:
            # Fatal error only on forbidden keys, else we would just warn, but parsing might fail
            raise
            
        ts = row["timestamp"]
        warnings = []
        
        if pd.isna(row["glucose_mgdl"]) and "glucose_mgdl" in sample and sample["glucose_mgdl"] is not None:
            warnings.append("Glucose out of range, set to NaN.")
            
        if self.last_timestamp is not None:
            if ts == self.last_timestamp:
                return self.get_state()
            if ts < self.last_timestamp:
                warnings.append("Late/out-of-order sample rejected.")
                s = self.get_state()
                s.data_quality.warnings.extend(warnings)
                return s
                
            gap_m = (ts - self.last_timestamp).total_seconds() / 60.0
            if gap_m > self.interval_m + 1e-3: # padding
                n_gaps = int(round(gap_m / self.interval_m)) - 1
                for i in range(1, n_gaps + 1):
                    pad_ts = self.last_timestamp + pd.Timedelta(minutes=self.interval_m * i)
                    pad_row = {
                        "timestamp": pad_ts,
                        "glucose_mgdl": np.nan,
                        "heart_rate": row["heart_rate"], # ffill approx
                        "steps": 0.0,
                        "sleep_state": "unknown", # explicit unknown
                        "meal_carbs_g": 0.0,
                        "activity_intensity": 0.0,
                        "patient_id": self.profile.patient_id
                    }
                    self.buffer.append(pad_row)
                    self._update_cumulative_state(pad_row)
                    
        self.buffer.append(row)
        self.last_timestamp = ts
        self._update_cumulative_state(row)
        
        # Trim buffer
        cutoff = ts - pd.Timedelta(minutes=self.history_buffer_m)
        self.buffer = [r for r in self.buffer if r["timestamp"] >= cutoff]
        
        return self._generate_state(warnings)
        
    def _apply_cumulative_overrides(self, last_feat: pd.Series):
        ts = last_feat["timestamp"]
        f_conf = self.config["features"]
        
        # meal_min_since_last
        if self.last_meal_ts is not None:
            mins = (ts - self.last_meal_ts).total_seconds() / 60.0
            last_feat["meal_min_since_last"] = min(mins, f_conf["max_minutes_since_meal"])
            last_feat["meal_any_in_history"] = 1.0
            last_feat["meal_last_carbs_g"] = self.last_meal_carbs
            
        # act_min_since_moderate
        if self.last_act_ts is not None:
            mins = (ts - self.last_act_ts).total_seconds() / 60.0
            last_feat["act_min_since_moderate"] = min(mins, f_conf["max_minutes_since_activity"])
            
        # sleep_min_since_wake
        if self.last_wake_ts is not None:
            mins = (ts - self.last_wake_ts).total_seconds() / 60.0
            if self.buffer[-1]["sleep_state"] not in ["awake", "unknown"]:
                last_feat["sleep_min_since_wake"] = 0.0
            else:
                last_feat["sleep_min_since_wake"] = min(mins, 720.0)
                
        # miss_min_since_last_obs
        if self.last_obs_ts is not None:
            mins = (ts - self.last_obs_ts).total_seconds() / 60.0
            last_feat["miss_min_since_last_obs"] = min(mins, 120.0)

    def _generate_state(self, warnings: List[str]) -> TwinState:
        if len(self.buffer) == 0:
            raise ValueError("Buffer is empty.")
            
        df_buf = pd.DataFrame(self.buffer)
        ts = df_buf["timestamp"].iloc[-1]
        
        # History available
        hist_hours = (ts - df_buf["timestamp"].iloc[0]).total_seconds() / 3600.0
        
        feat_df = build_features_for_patient(df_buf, self.profile_series, self.config)
        last_feat = feat_df.iloc[-1].copy()
        
        # Override cumulatives
        self._apply_cumulative_overrides(last_feat)
        
        # Cache the fixed feature vector for explain_row if requested
        self._last_feature_row = pd.DataFrame([last_feat])
        
        # Data Quality
        mins_since_obs = last_feat["miss_min_since_last_obs"]
        comp_60m = 1.0 - last_feat["miss_glucose_frac_60m"]
        
        dq_status = "ok"
        confidence = "high"
        
        if hist_hours < self.config["twin"]["warmup_hours"]:
            dq_status = "warming_up"
            confidence = "low"
        elif pd.isna(last_feat["glu_current"]):
            if mins_since_obs >= self.config["twin"]["stale_data_minutes"]:
                dq_status = "stale"
                confidence = "low"
            else:
                dq_status = "no_glucose"
                confidence = "medium"
        elif comp_60m < self.config["twin"]["min_completeness_60m"]:
            dq_status = "low_completeness"
            confidence = "medium"
            
        dq = DataQuality(
            status=dq_status,
            minutes_since_last_glucose=float(mins_since_obs),
            completeness_60m=float(comp_60m),
            history_hours_available=float(hist_hours),
            warnings=warnings,
            confidence=confidence
        )
        
        # Trend
        d30 = last_feat["glu_delta_30m"]
        tdir = "stable"
        if not pd.isna(d30):
            rate = d30 / 6.0 # rate per 5 mins
            th = self.config["twin"]["trend_thresholds"]
            if rate >= th["rising_fast"]: tdir = "rising_fast"
            elif rate >= th["rising"]: tdir = "rising"
            elif rate <= th["falling_fast"]: tdir = "falling_fast"
            elif rate <= th["falling"]: tdir = "falling"
            
        g_sum = GlucoseSummary(
            current_glucose=float(last_feat["glu_current"]) if not pd.isna(last_feat["glu_current"]) else None,
            trend_30m=float(d30) if not pd.isna(d30) else None,
            trend_direction=tdir,
            time_in_range_24h=float(last_feat.get("pers_time_in_range_24h", np.nan))
        )
        
        ctx = TwinContext(
            minutes_since_last_meal=float(last_feat["meal_min_since_last"]),
            carbs_on_board_estimate=float(last_feat["meal_cob_estimate"]),
            minutes_since_last_activity=float(last_feat["act_min_since_moderate"]),
            sleep_state=self.buffer[-1]["sleep_state"]
        )
        
        meas = Measurement(
            timestamp=ts.isoformat(),
            glucose_mgdl=float(self.buffer[-1]["glucose_mgdl"]) if not pd.isna(self.buffer[-1]["glucose_mgdl"]) else None,
            heart_rate=float(self.buffer[-1]["heart_rate"]),
            steps=float(self.buffer[-1]["steps"]),
            sleep_state=self.buffer[-1]["sleep_state"],
            meal_carbs_g=float(self.buffer[-1]["meal_carbs_g"]),
            activity_intensity=float(self.buffer[-1]["activity_intensity"])
        )
        
        # Risk
        risk = None
        alert = None
        
        if dq_status != "warming_up":
            # predict
            features_list = self.pipeline.feature_names_in_ # assuming XGB
            X = self._last_feature_row[features_list]
            prob_raw = float(self.pipeline.predict_proba(X)[:, 1][0])
            
            # manual apply calibrator logic since we might not have the module handy here
            if hasattr(self.calibrator, "transform"):
                prob_calib = float(np.clip(self.calibrator.transform([prob_raw])[0], 0, 1))
            else:
                prob_calib = float(np.clip(self.calibrator.predict_proba(np.array([[prob_raw]]))[:, 1][0], 0, 1))
                
            t_med = self.thresholds["t_medium"]
            t_high = self.thresholds["t_high"]
            
            band = "Low"
            if prob_calib >= t_high: band = "High"
            elif prob_calib >= t_med: band = "Medium"
            
            drivers = []
            if band in ["Medium", "High"] and self.explainer is not None:
                drivers = self.get_drivers(self.config["twin"]["drivers_top_k"])
                
            risk = RiskAssessment(
                probability_calibrated=prob_calib,
                probability_raw=prob_raw,
                band=band,
                band_thresholds={"Medium": t_med, "High": t_high},
                drivers=drivers,
                model_version="v1" # simplified
            )
            
            # Alert Logic
            if band in ["Medium", "High"]:
                fire = False
                if len(self.alert_history) == 0:
                    fire = True
                else:
                    last_al = self.alert_history[-1]
                    last_al_ts = pd.to_datetime(last_al.timestamp)
                    mins_since = (ts - last_al_ts).total_seconds() / 60.0
                    if mins_since >= self.config["twin"]["alert_cooldown_minutes"]:
                        fire = True
                    elif band == "High" and last_al.band == "Medium":
                        fire = True # escalation
                        
                if fire:
                    alert = AlertEvent(
                        timestamp=ts.isoformat(),
                        band=band,
                        probability=prob_calib,
                        message=f"{band} risk detected ({prob_calib:.0%})."
                    )
                    self.alert_history.append(alert)
                    
            self.risk_history.append({"timestamp": ts.isoformat(), "prob": prob_calib, "band": band})
            
            # Trim risk history
            cutoff_risk = ts - pd.Timedelta(hours=self.config["twin"]["risk_history_hours"])
            self.risk_history = [r for r in self.risk_history if pd.to_datetime(r["timestamp"]) >= cutoff_risk]

        return TwinState(
            profile=self.profile,
            latest_measurement=meas,
            risk=risk,
            data_quality=dq,
            forecast=None,
            forecast_status="not_available",
            active_alert=alert,
            glucose_summary=g_sum,
            context=ctx,
            timestamp=ts.isoformat(),
            engine_version="1.0.0"
        )

    def ingest_batch(self, samples: list[dict]) -> list[TwinState]:
        return [self.ingest(s) for s in samples]

    def update_profile(self, **kwargs):
        prof_dict = self.profile.to_dict()
        for k, v in kwargs.items():
            if k in prof_dict:
                prof_dict[k] = v
            else:
                raise ValueError(f"Invalid profile field: {k}")
        self.profile = PatientProfile.from_dict(prof_dict)
        self.profile_series = pd.Series(self.profile.to_dict())

    def get_state(self) -> TwinState:
        if not self.buffer:
            raise ValueError("No state available, buffer empty.")
        return self._generate_state([])

    def get_drivers(self, top_k: int = 3) -> List[Dict[str, Any]]:
        if not hasattr(self, "_last_feature_row") or self.explainer is None:
            return []
        features_list = self.pipeline.feature_names_in_
        return explain_row(self.explainer, self._last_feature_row, features_list, top_k=top_k)

    def snapshot(self) -> dict:
        return {
            "profile": self.profile.to_dict(),
            "buffer": [{"timestamp": r["timestamp"].isoformat()} | {k: v for k, v in r.items() if k != "timestamp"} for r in self.buffer],
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
            "cumulatives": {
                "last_meal_ts": self.last_meal_ts.isoformat() if self.last_meal_ts else None,
                "last_meal_carbs": self.last_meal_carbs,
                "last_act_ts": self.last_act_ts.isoformat() if self.last_act_ts else None,
                "last_wake_ts": self.last_wake_ts.isoformat() if self.last_wake_ts else None,
                "last_obs_ts": self.last_obs_ts.isoformat() if self.last_obs_ts else None
            },
            "alert_history": [a.to_dict() for a in self.alert_history],
            "risk_history": self.risk_history
        }

    @classmethod
    def restore(cls, data: dict, pipeline, calibrator, thresholds, config, explainer=None) -> "DiaTwin":
        prof = PatientProfile.from_dict(data["profile"])
        twin = cls(prof, pipeline, calibrator, thresholds, config, explainer)
        
        twin.buffer = [{"timestamp": pd.to_datetime(r["timestamp"])} | {k: v for k, v in r.items() if k != "timestamp"} for r in data["buffer"]]
        twin.last_timestamp = pd.to_datetime(data["last_timestamp"]) if data["last_timestamp"] else None
        
        cums = data["cumulatives"]
        twin.last_meal_ts = pd.to_datetime(cums["last_meal_ts"]) if cums["last_meal_ts"] else None
        twin.last_meal_carbs = cums["last_meal_carbs"]
        twin.last_act_ts = pd.to_datetime(cums["last_act_ts"]) if cums["last_act_ts"] else None
        twin.last_wake_ts = pd.to_datetime(cums["last_wake_ts"]) if cums["last_wake_ts"] else None
        twin.last_obs_ts = pd.to_datetime(cums["last_obs_ts"]) if cums["last_obs_ts"] else None
        
        twin.alert_history = [AlertEvent.from_dict(a) for a in data["alert_history"]]
        twin.risk_history = data["risk_history"]
        
        return twin
