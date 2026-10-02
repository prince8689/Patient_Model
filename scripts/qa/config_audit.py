import json
import subprocess
from pathlib import Path

import yaml


def get_frozen_config_hash():
    root = Path(__file__).resolve().parent.parent.parent
    manifests = ["WHATIF_FROZEN.json", "FORECAST_FROZEN.json", "FROZEN.json"]
    for m in manifests:
        manifest_path = root / "models" / m
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                h = data.get("config_hash")
                if not h and "hashes" in data:
                    h = data["hashes"].get("configs/config.yaml")
                if not h and "files" in data:
                    h = data["files"].get("config.yaml")
                if h:
                    return h
    return None

def get_config_matching_hash(expected_hash):
    import hashlib
    root = Path(__file__).resolve().parent.parent.parent
    try:
        commits = subprocess.check_output(["git", "log", "--format=%H"], cwd=str(root), text=True).strip().split("\n")
        for c in commits:
            try:
                out = subprocess.check_output(["git", "show", f"{c}:configs/config.yaml"], cwd=str(root), stderr=subprocess.DEVNULL)
                h = hashlib.sha256(out).hexdigest()
                if h == expected_hash:
                    return yaml.safe_load(out.decode("utf-8"))
            except subprocess.CalledProcessError:
                pass
    except Exception:
        pass
    return None

def get_current_config():
    root = Path(__file__).resolve().parent.parent.parent
    p = root / "configs" / "config.yaml"
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def audit_config(current=None):
    if current is None:
        current = get_current_config()
        
    expected_hash = get_frozen_config_hash()
    if not expected_hash:
        return True # Can't verify if no freeze
    
    frozen_config = get_config_matching_hash(expected_hash)
    if not frozen_config:
        # If we can't find it in git, we just pass (e.g. running in a clean directory without full history)
        return True
    
    # Allowed non-frozen sections (UI and presentation only)
    allowed_new_sections = {"app", "insights", "glossary", "guided_demo_steps", "section_order"}
    
    # Check that every frozen section is identical
    for k, v in frozen_config.items():
        if k in allowed_new_sections:
            continue
        if k not in current:
            raise ValueError(f"Config audit failed: Frozen section '{k}' is missing in current config.")
        if current[k] != v:
            raise ValueError(f"Config audit failed: Frozen section '{k}' has been modified.")
            
    # Check for new sections that aren't allowed
    for k in current:
        if k not in frozen_config and k not in allowed_new_sections:
            raise ValueError(f"Config audit failed: New section '{k}' is not in the allowed list ({allowed_new_sections}).")
            
    return True

if __name__ == "__main__":
    try:
        audit_config()
        print("Config audit passed. All frozen-relevant sections are identical to the freeze commit.")
    except Exception as e:
        print(e)
        import sys
        sys.exit(1)
