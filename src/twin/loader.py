import hashlib
import json
import logging
from pathlib import Path

import joblib
import pandas as pd

from src.twin.engine import DiaTwin
from src.twin.state import PatientProfile


def get_file_sha256(filepath: Path) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_frozen_artifacts(config: dict):
    frozen_path = Path(config["evaluation"]["frozen_manifest_path"])
    if not frozen_path.exists():
        raise FileNotFoundError("FROZEN.json not found.")
        
    with open(frozen_path, "r") as f:
        frozen = json.load(f)
        
    for fp_str, expected_hash in frozen["hashes"].items():
        fp = Path(fp_str)
        if not fp.exists():
            raise FileNotFoundError(f"Frozen artifact missing: {fp}")
        if "config.yaml" in fp.name:
            import sys
            # Ensure scripts module is reachable
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
            from scripts.qa.config_audit import audit_config
            audit_config()
            continue
            
        actual_hash = get_file_sha256(fp)
        if actual_hash != expected_hash:
            raise ValueError(f"FROZEN HASH MISMATCH! {fp} has been modified.\nExpected: {expected_hash}\nActual: {actual_hash}")
            
    models_path = Path(config["paths"]["models"])
    pipeline = joblib.load(models_path / "xgb_v1.joblib")
    try:
        calibrator = joblib.load(models_path / "calibrator_v1.joblib")
    except Exception as e:
        import logging
        logging.warning(f"Failed to load calibrator, using identity fallback. Error: {e}")
        class DummyCalib:
            def transform(self, x): return x
            def predict_proba(self, x): 
                import numpy as np
                return np.column_stack([1-x, x])
        calibrator = DummyCalib()
    
    with open(models_path / "thresholds_v1.json", "r") as f:
        thresholds = json.load(f)["thresholds"]
        
    with open(models_path / "xgb_v1_meta.json", "r") as f:
        meta = json.load(f)
        
    return pipeline, calibrator, thresholds, meta

def load_forecast_artifacts(config: dict):
    if "forecast" not in config or "manifest_path" not in config["forecast"]:
        return None
    manifest_path = Path(config["forecast"]["manifest_path"])
    if not manifest_path.exists():
        return None
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    models_dir = Path(config["forecast"]["models_dir"])
    files_to_hash = [
        models_dir / "forecaster_v1.joblib",
        models_dir / "forecaster_v1_meta.json",
        models_dir / "forecast_conformal_v1.json",
        Path("configs") / "config.yaml"
    ]
    for fp in files_to_hash:
        if not fp.exists():
            return None
        if "config.yaml" in fp.name:
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
            from scripts.qa.config_audit import audit_config
            audit_config()
            continue
            
        actual_hash = get_file_sha256(fp)
        expected = manifest["files"].get(fp.name)
        if actual_hash != expected:
            raise ValueError(f"FORECAST HASH MISMATCH! {fp} has been modified.\nExpected: {expected}\nActual: {actual_hash}")
            
    models = joblib.load(models_dir / "forecaster_v1.joblib")
    with open(models_dir / "forecaster_v1_meta.json", "r") as f:
        meta = json.load(f)
    with open(models_dir / "forecast_conformal_v1.json", "r") as f:
        calib = json.load(f)
        
    from src.forecast.conformal import ConformalCalibrator
    calibrator = ConformalCalibrator(meta["horizons"], meta["quantiles"], config["forecast"]["nominal_interval_coverage"])
    calibrator.q_hat = {int(k): v for k, v in calib["q_hat"].items()}
    
    return models["xgb"], calibrator, meta

def load_whatif_artifacts(config: dict):
    if "whatif" not in config or "manifest_path" not in config["whatif"]:
        return None
    manifest_path = Path(config["whatif"]["manifest_path"])
    if not manifest_path.exists():
        return None
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    prior_path = Path(config["whatif"]["prior_path"])
    if not prior_path.exists():
        return None
        
    actual_hash = get_file_sha256(prior_path)
    if actual_hash != manifest.get("whatif_prior_hash"):
        raise ValueError(f"WHATIF HASH MISMATCH! {prior_path} has been modified.\nExpected: {manifest.get('whatif_prior_hash')}\nActual: {actual_hash}")
        
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from scripts.qa.config_audit import audit_config
    audit_config()
        
    with open(prior_path, "r") as f:
        prior_data = json.load(f)
        
    return prior_data

class TwinRegistry:
    def __init__(self, config: dict):
        self.config = config
        self.twins = {}
        
        # Load artifacts once
        self.pipeline, self.calibrator, self.thresholds, self.meta = load_frozen_artifacts(config)
        self.forecast_artifacts = load_forecast_artifacts(config)
        self.whatif_artifacts = load_whatif_artifacts(config)
        
        # Try to load explainer
        try:
            import shap
            self.explainer = shap.TreeExplainer(self.pipeline)
        except Exception as e:
            logging.warning(f"Failed to load SHAP Explainer: {e}. Drivers will be empty.")
            self.explainer = None
            
        patients_df = pd.read_csv(Path(config["paths"]["data_raw"]) / "patients.csv")
        self.patient_profiles = {row["patient_id"]: PatientProfile(**row[PatientProfile.__annotations__.keys()].to_dict()) 
                                 for _, row in patients_df.iterrows()}
        
    def register(self, patient_id: str) -> DiaTwin:
        if patient_id not in self.patient_profiles:
            raise ValueError(f"Unknown patient {patient_id}")
        twin = DiaTwin(
            profile=self.patient_profiles[patient_id],
            pipeline=self.pipeline,
            calibrator=self.calibrator,
            thresholds=self.thresholds,
            config=self.config,
            explainer=self.explainer,
            forecast_artifacts=self.forecast_artifacts,
            whatif_artifacts=self.whatif_artifacts
        )
        self.twins[patient_id] = twin
        return twin
        
    def get(self, patient_id: str) -> DiaTwin:
        if patient_id not in self.twins:
            return self.register(patient_id)
        return self.twins[patient_id]
        
    def list_patients(self) -> list:
        res = []
        for pid, twin in self.twins.items():
            state = None
            if twin.buffer:
                state = twin.get_state()
            res.append({
                "patient_id": pid,
                "age": twin.profile.age,
                "sex": twin.profile.sex,
                "hba1c": twin.profile.hba1c,
                "band": state.risk.band if state and state.risk else "N/A",
                "last_update": state.timestamp if state else "N/A"
            })
        return res
        
    def ingest(self, patient_id: str, sample: dict):
        twin = self.get(patient_id)
        return twin.ingest(sample)
