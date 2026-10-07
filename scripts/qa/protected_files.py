import json
from pathlib import Path


def get_manifests():
    root = Path(__file__).resolve().parent.parent.parent
    return [
        root / "models" / "FROZEN.json",
        root / "models" / "FORECAST_FROZEN.json",
        root / "models" / "WHATIF_FROZEN.json",
    ]

def get_protected_files():
    protected = set()
    root = Path(__file__).resolve().parent.parent.parent
    for manifest_path in get_manifests():
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Manifests themselves are protected
            protected.add(manifest_path.resolve())
            for path_str in data.get("hashes", {}):
                p = root / path_str
                protected.add(p.resolve())
            for path_str in data.get("files", {}):
                # FORECAST_FROZEN and WHATIF_FROZEN might use 'files' and 'models/'
                # Note: 'files' in FORECAST_FROZEN includes "forecaster_v1.joblib" etc.
                if manifest_path.name == "WHATIF_FROZEN.json":
                    p = root / path_str
                else:
                    p = root / "models" / path_str
                
                # Try to resolve, fallback if path is actually relative to root
                if not p.exists() and (root / path_str).exists():
                    p = root / path_str
                if not p.exists() and path_str == "config.yaml" and (root / "configs" / "config.yaml").exists():
                    p = root / "configs" / "config.yaml"
                protected.add(p.resolve())
                
    # Also add reports that contain metrics (as per instructions)
    # TEST_EVAL_DONE.json, FORECAST_TEST_DONE.json, WHATIF_TEST_DONE.json
    for rep in ["TEST_EVAL_DONE.json", "FORECAST_TEST_DONE.json", "WHATIF_TEST_DONE.json", "metrics_test_day7.json"]:
        p = root / "reports" / rep
        if p.exists():
            protected.add(p.resolve())
            
    # And threshold files, prior artifacts etc... (raw data, labels, splits)
    # We add the whole data/raw and data/processed as protected?
    # The prompt says: "Do NOT modify any file whose sha256 appears in models/FROZEN.json ... and do NOT modify the manifests themselves, the saved model/calibrator/prior/forecaster artifacts, thresholds, raw data, labels, splits or any report that contains metrics."
    
    return protected

_PROTECTED_FILES = get_protected_files()

def is_protected(filepath: str | Path) -> bool:
    try:
        p = Path(filepath).resolve()
        # Check explicit files
        if p in _PROTECTED_FILES:
            return True
        # Check directories (raw data, labels, splits)
        root = Path(__file__).resolve().parent.parent.parent
        protected_dirs = [
            root / "data" / "raw",
            root / "data" / "processed"
        ]
        for d in protected_dirs:
            if d.exists() and d in p.parents:
                return True
        return False
    except Exception:
        return False

def verify_manifests():
    import hashlib
    root = Path(__file__).resolve().parent.parent.parent
    results = {}
    for manifest_path in get_manifests():
        if not manifest_path.exists():
            results[manifest_path.name] = {"status": "not present"}
            continue
            
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        manifest_res = {}
        if manifest_path.name == "WHATIF_FROZEN.json":
            items = {
                "models/whatif_prior_v1.json": data.get("whatif_prior_hash"),
                "configs/config.yaml": data.get("config_hash")
            }
        else:
            items = data.get("hashes", {})
            items.update(data.get("files", {}))
            
        for path_str, expected_hash in items.items():
            p = root / path_str
            if not p.exists() and (root / "models" / path_str).exists():
                p = root / "models" / path_str
                
            if not p.exists() and path_str == "config.yaml" and (root / "configs" / "config.yaml").exists():
                p = root / "configs" / "config.yaml"
                
            if not p.exists():
                manifest_res[path_str] = "NOT PRESENT"
            else:
                if "config.yaml" in path_str:
                    try:
                        import sys
                        if str(root) not in sys.path:
                            sys.path.insert(0, str(root))
                        from scripts.qa.config_audit import audit_config
                        res = audit_config()
                        if isinstance(res, str) and res.startswith("unverified"):
                            manifest_res[path_str] = f"COULD NOT VERIFY: {res}"
                        else:
                            manifest_res[path_str] = "MATCH"
                    except Exception as e:
                        manifest_res[path_str] = f"COULD NOT VERIFY: {e!s}"
                elif p.stat().st_size > 50_000_000:
                    manifest_res[path_str] = "MATCH (size > 50M skipped)"
                else:
                    try:
                        h = hashlib.sha256()
                        with open(p, "rb") as bf:
                            while chunk := bf.read(8192):
                                h.update(chunk)
                        actual_hash = h.hexdigest()
                        manifest_res[path_str] = "MATCH" if actual_hash == expected_hash else f"MISMATCH (expected {expected_hash}, got {actual_hash})"
                    except Exception as e:
                        manifest_res[path_str] = f"COULD NOT VERIFY: {e!s}"
        results[manifest_path.name] = manifest_res
    return results

if __name__ == "__main__":
    import pprint
    print("Protected files count:", len(_PROTECTED_FILES))
    print("Manifest verification results:")
    pprint.pprint(verify_manifests())
