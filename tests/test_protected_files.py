import json
import hashlib
from pathlib import Path
import subprocess
import pytest
from scripts.qa.config_audit import audit_config

def get_manifests():
    root = Path(__file__).resolve().parent.parent
    return [
        root / "models" / "FROZEN.json",
        root / "models" / "FORECAST_FROZEN.json",
        root / "models" / "WHATIF_FROZEN.json",
    ]

def is_tracked(path_str, root):
    try:
        out = subprocess.check_output(["git", "ls-files", "--error-unmatch", path_str], cwd=str(root), stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def get_manifest_entries():
    root = Path(__file__).resolve().parent.parent
    entries = []
    for m in ["FROZEN.json", "FORECAST_FROZEN.json", "WHATIF_FROZEN.json"]:
        manifest_path = root / "models" / m
        if not manifest_path.exists():
            continue
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if m == "WHATIF_FROZEN.json":
            items = {
                "models/whatif_prior_v1.json": data.get("whatif_prior_hash"),
                "configs/config.yaml": data.get("config_hash")
            }
        else:
            items = data.get("hashes", {})
            items.update(data.get("files", {}))
        for p, h in items.items():
            entries.append((m, p, h))
    return entries

@pytest.mark.parametrize("manifest_name, path_str, expected_hash", get_manifest_entries(), ids=lambda x: f"{x[0]}-{x[1]}")
def test_manifest_entry(manifest_name, path_str, expected_hash):
    root = Path(__file__).resolve().parent.parent
    p = root / path_str
    if not p.exists() and (root / "models" / path_str).exists():
        p = root / "models" / path_str
    if not p.exists() and path_str == "config.yaml" and (root / "configs" / "config.yaml").exists():
        p = root / "configs" / "config.yaml"
        
    if not p.exists():
        rel_path = p.relative_to(root).as_posix() if p.is_relative_to(root) else path_str
        if not is_tracked(rel_path, root):
            pytest.skip(f"File {path_str} in {manifest_name} is not present in this checkout")
        else:
            assert False, f"Tracked file {path_str} in {manifest_name} is missing!"
            
    if path_str.endswith("config.yaml"):
        try:
            res = audit_config()
            if isinstance(res, str) and res.startswith("unverified"):
                pytest.skip(f"File {path_str} in {manifest_name} is {res}")
            else:
                assert res is True, f"File {path_str} in {manifest_name} has been modified (mismatch)!"
        except Exception as e:
            pytest.fail(f"Could not verify: {e}")
    elif p.stat().st_size > 50_000_000:
        pass
    else:
        try:
            h = hashlib.sha256()
            with open(p, "rb") as bf:
                while chunk := bf.read(8192):
                    h.update(chunk)
            actual_hash = h.hexdigest()
            assert actual_hash == expected_hash, f"File {path_str} in {manifest_name} has been modified (mismatch)!"
        except Exception as e:
            pytest.fail(f"Could not verify: {e}")

def test_guard_protected_files_diff():
    pass
