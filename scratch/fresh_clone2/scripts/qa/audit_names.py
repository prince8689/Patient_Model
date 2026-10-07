import os
import re
import csv
from pathlib import Path
import json

PROTECTED_DIRS = ["data/raw", "data/processed", "models", "configs"]
PROTECTED_EXTENSIONS = [".json", ".parquet", ".csv", ".joblib", ".pkl", ".yaml"]

def load_frozen_manifests():
    frozen_files = set()
    manifests = ["models/FROZEN.json", "models/FORECAST_FROZEN.json", "models/WHATIF_FROZEN.json"]
    for m in manifests:
        frozen_files.add(m.replace("/", os.sep))
        with open(m, "r") as f:
            data = json.load(f)
            for file_path in data.get("hashes", {}).keys():
                frozen_files.add(file_path.replace("/", os.sep))
    return frozen_files

def is_protected(filepath_str: str, frozen_files: set) -> bool:
    norm_path = filepath_str.replace("/", os.sep)
    if norm_path in frozen_files:
        return True
    # If it is a report file holding metrics (json/csv)
    if norm_path.startswith("reports" + os.sep) and (norm_path.endswith(".json") or norm_path.endswith(".csv") or norm_path.endswith(".parquet")):
        return True
    if norm_path == "configs" + os.sep + "config.yaml":
        return True
    return False

def find_rename_candidates(root_dir: Path):
    patterns = [r"day\d+", r"step\d+", r"phase\d+", r"stage_\d+", r"v1_final", r"tmp", r"new", r"old", r"copy", r"test2"]
    regex = re.compile("|".join(patterns), re.IGNORECASE)
    
    frozen_files = load_frozen_manifests()
    
    candidates = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        rel_dir = Path(dirpath).relative_to(root_dir)
        if ".git" in rel_dir.parts or ".venv" in rel_dir.parts or "__pycache__" in rel_dir.parts or ".pytest_cache" in rel_dir.parts:
            continue
            
        for d in dirnames:
            if regex.search(d):
                rel_path = (rel_dir / d).as_posix()
                protected = False
                candidates.append({
                    "old_path": rel_path,
                    "protected": protected,
                    "type": "dir"
                })
                
        for f in filenames:
            if regex.search(f):
                rel_path = (rel_dir / f).as_posix()
                protected = is_protected(rel_path, frozen_files)
                candidates.append({
                    "old_path": rel_path,
                    "protected": protected,
                    "type": "file"
                })
                
    return candidates

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent.parent
    cands = find_rename_candidates(root)
    with open("reports/qa/audit_names.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["old_path", "protected", "type"])
        writer.writeheader()
        writer.writerows(cands)
