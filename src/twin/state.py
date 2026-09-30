from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class PatientProfile:
    patient_id: str
    age: float
    sex: str
    bmi: float
    hba1c: float
    diabetes_duration_years: float
    on_insulin: int
    on_metformin: int
    hypertension: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PatientProfile":
        if "baseline_insulin_sensitivity" in data:
            raise ValueError("PatientProfile cannot contain forbidden sim parameters.")
        return cls(**data)

@dataclass
class Measurement:
    timestamp: str
    glucose_mgdl: Optional[float]
    heart_rate: float
    steps: float
    sleep_state: str
    meal_carbs_g: float
    activity_intensity: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Measurement":
        return cls(**data)

@dataclass
class RiskAssessment:
    probability_calibrated: float
    probability_raw: float
    band: str
    band_thresholds: Dict[str, float]
    drivers: List[Dict[str, Any]]
    model_version: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RiskAssessment":
        return cls(**data)

@dataclass
class DataQuality:
    status: str  # "ok", "warming_up", "stale", "low_completeness", "no_glucose"
    minutes_since_last_glucose: float
    completeness_60m: float
    history_hours_available: float
    warnings: List[str]
    confidence: str  # "high", "medium", "low"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DataQuality":
        return cls(**data)

@dataclass
class AlertEvent:
    timestamp: str
    band: str
    probability: float
    message: str
    acknowledged: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AlertEvent":
        return cls(**data)

@dataclass
class GlucoseSummary:
    current_glucose: Optional[float]
    trend_30m: Optional[float]
    trend_direction: str  # "rising_fast", "rising", "stable", "falling", "falling_fast"
    time_in_range_24h: Optional[float]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GlucoseSummary":
        return cls(**data)

@dataclass
class TwinContext:
    minutes_since_last_meal: float
    carbs_on_board_estimate: float
    minutes_since_last_activity: float
    sleep_state: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TwinContext":
        return cls(**data)

@dataclass
class ForecastResult:
    status: str
    horizons_minutes: List[int]
    quantiles: Dict[str, List[float]]
    trajectory_5min: Dict[str, List[float]]
    predicted_peak: float
    predicted_peak_minutes: int
    predicted_min: float
    predicted_min_minutes: int
    hypo_risk_flag: bool
    hyper_risk_flag: bool
    time_above_180_expected_minutes: float
    agreement_with_risk_band: bool
    model_version: str
    summary: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastResult":
        return cls(**data)

@dataclass
class TwinState:
    profile: PatientProfile
    latest_measurement: Measurement
    risk: Optional[RiskAssessment]
    data_quality: DataQuality
    forecast: Optional[ForecastResult]
    forecast_status: str
    active_alert: Optional[AlertEvent]
    glucose_summary: GlucoseSummary
    context: TwinContext
    timestamp: str
    engine_version: str

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.risk is None:
            d["risk"] = None
        if self.active_alert is None:
            d["active_alert"] = None
        if self.forecast is None:
            d["forecast"] = None
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "TwinState":
        d = data.copy()
        d["profile"] = PatientProfile.from_dict(d["profile"])
        d["latest_measurement"] = Measurement.from_dict(d["latest_measurement"])
        if d.get("risk"):
            d["risk"] = RiskAssessment.from_dict(d["risk"])
        d["data_quality"] = DataQuality.from_dict(d["data_quality"])
        if d.get("forecast"):
            d["forecast"] = ForecastResult.from_dict(d["forecast"])
        if d.get("active_alert"):
            d["active_alert"] = AlertEvent.from_dict(d["active_alert"])
        d["glucose_summary"] = GlucoseSummary.from_dict(d["glucose_summary"])
        d["context"] = TwinContext.from_dict(d["context"])
        return cls(**d)
