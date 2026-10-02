import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path


def get_file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def main():
    models_dir = Path("models")
    
    files_to_hash = [
        models_dir / "forecaster_v1.joblib",
        models_dir / "forecaster_v1_meta.json",
        models_dir / "forecast_conformal_v1.json",
        Path("configs") / "config.yaml"
    ]
    
    hashes = {}
    for f in files_to_hash:
        hashes[f.name] = get_file_hash(f)
        
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    
    manifest = {
        "timestamp": datetime.utcnow().isoformat(),
        "git_commit": commit_hash,
        "files": hashes
    }
    
    with open(models_dir / "FORECAST_FROZEN.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    print("Forecast frozen successfully.")

if __name__ == "__main__":
    main()
