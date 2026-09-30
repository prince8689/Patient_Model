import sys
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.features.registry import FEATURE_REGISTRY

def get_file_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "unknown"

def main():
    config = load_config()
    models_path = Path(config["paths"]["models"])
    
    files_to_hash = [
        models_path / "xgb_v1.joblib",
        models_path / "xgb_v1_meta.json",
        models_path / "calibrator_v1.joblib",
        models_path / "thresholds_v1.json",
        Path("configs/config.yaml"),
        Path("src/features/registry.py")
    ]
    
    hashes = {}
    for fp in files_to_hash:
        if not fp.exists():
            print(f"Error: Required file {fp} does not exist. Cannot freeze.")
            sys.exit(1)
        hashes[str(fp.as_posix())] = get_file_sha256(fp)
        
    features = [f["name"] for f in FEATURE_REGISTRY]
    
    frozen = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "hashes": hashes,
        "features": features
    }
    
    frozen_path = Path(config["evaluation"]["frozen_manifest_path"])
    with open(frozen_path, "w") as f:
        json.dump(frozen, f, indent=2)
        
    print(f"Successfully froze model state to {frozen_path}")
    print(json.dumps(frozen, indent=2))

if __name__ == "__main__":
    main()
