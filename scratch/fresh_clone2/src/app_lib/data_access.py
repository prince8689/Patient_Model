import functools
import logging
from pathlib import Path

import pandas as pd

from src.utils.config import load_config


class AppStartupError(Exception):
    pass

@functools.lru_cache(maxsize=1)
def get_config():
    return load_config()

@functools.lru_cache(maxsize=1)
def get_registry():
    config = get_config()
    if config["app"].get("use_demo_bundle"):
        # Dummy registry for demo bundle
        class DummyRegistry:
            def list_patients(self):
                return []
        return DummyRegistry()
        
    try:
        from src.twin.loader import TwinRegistry
        return TwinRegistry(config)
    except Exception as e:
        logging.error(f"Failed to load TwinRegistry: {e}")
        raise AppStartupError(f"Failed to load twin engine or verify frozen artifacts. Error: {e}")

@functools.lru_cache(maxsize=1)
def get_demo_patients():
    config = get_config()
    if config["app"].get("use_demo_bundle"):
        bundle_dir = Path("demo_bundle")
        if not bundle_dir.exists():
            raise AppStartupError("Demo bundle directory not found.")
        df = pd.read_csv(bundle_dir / "patients.csv")
        return df["patient_id"].tolist()
        
    # Get patients from demo split
    splits_path = Path(config["paths"]["data_processed"]) / "splits.csv"
    if not splits_path.exists():
        raise AppStartupError(f"Splits file not found: {splits_path}")
    splits = pd.read_csv(splits_path)
    
    demo_split = config["twin"].get("demo_patient_split", "test")
    demo_pids = splits[splits["split"] == demo_split]["patient_id"].values
    
    predefined = config["app"].get("demo_patient_ids")
    if predefined:
        return [p for p in predefined if p in demo_pids]
        
    # Auto-pick 6 from demo split based on HbA1c tertiles
    patients_df = get_patients_df()
    demo_prof = patients_df[patients_df["patient_id"].isin(demo_pids)].copy()
    if demo_prof.empty:
        return []
        
    demo_prof["tertile"] = pd.qcut(demo_prof["hba1c"], 3, labels=["Low", "Med", "High"])
    picked = []
    for t in ["Low", "Med", "High"]:
        t_pats = demo_prof[demo_prof["tertile"] == t]["patient_id"].tolist()
        picked.extend(t_pats[:2])
    return picked

@functools.lru_cache(maxsize=1)
def get_patients_df():
    config = get_config()
    if config["app"].get("use_demo_bundle"):
        return pd.read_csv("demo_bundle/patients.csv")
    return pd.read_csv(Path(config["paths"]["data_raw"]) / "patients.csv")

@functools.lru_cache(maxsize=100)
def get_patient_timeline(patient_id: str):
    config = get_config()
    if config["app"].get("use_demo_bundle"):
        return pd.read_parquet(f"demo_bundle/timelines/{patient_id}.parquet")
        
    timeline_dir = Path(config["paths"]["data_processed"]) / "twin_timelines"
    file_path = timeline_dir / f"{patient_id}.parquet"
    if file_path.exists():
        return pd.read_parquet(file_path)
        
    # Build it if missing
    from src.twin.timeline import generate_timeline_for_patient
    registry = get_registry()
    generate_timeline_for_patient(patient_id, config, registry)
    return pd.read_parquet(file_path)

@functools.lru_cache(maxsize=100)
def get_patient_wearable(patient_id: str):
    config = get_config()
    if config["app"].get("use_demo_bundle"):
        return pd.read_parquet(f"demo_bundle/wearable/{patient_id}.parquet")
        
    # Try processed
    w_path = Path(config["paths"]["data_processed"]) / "wearable" / f"{patient_id}.parquet"
    if w_path.exists():
        return pd.read_parquet(w_path)
    
    # Try raw
    w_raw = Path(config["paths"]["data_raw"]) / "wearable.csv"
    if w_raw.exists():
        df = pd.read_csv(w_raw)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df[df["patient_id"] == patient_id].copy()
        
    raise AppStartupError(f"No wearable data found for {patient_id}")
