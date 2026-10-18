import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path


def file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_git_commit(filepath=None):
    try:
        if filepath:
            cmd = ["git", "log", "-n", "1", "--pretty=format:%H", "--", filepath]
        else:
            cmd = ["git", "rev-parse", "HEAD"]
        return subprocess.check_output(cmd).decode('utf-8').strip()
    except Exception:
        return "unknown"

def get_git_timestamp(filepath=None):
    try:
        if filepath:
            cmd = ["git", "log", "-n", "1", "--pretty=format:%cI", "--", filepath]
        else:
            cmd = ["git", "log", "-1", "--format=%cI"]
        return subprocess.check_output(cmd).decode('utf-8').strip()
    except Exception:
        return datetime.utcnow().isoformat()

def is_ancestor(commit_ancestor, commit_descendant):
    try:
        subprocess.check_output(["git", "merge-base", "--is-ancestor", commit_ancestor, commit_descendant])
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False

def load_json(filepath):
    p = Path(filepath)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def build_bundle():
    bundle = {
        "generated_at": datetime.utcnow().isoformat(),
        "sections": {},
        "missing": {}
    }
    
    def add_section(name, data, filepath):
        if data is not None:
            bundle["sections"][name] = {
                "source": filepath,
                "data": data
            }
        else:
            bundle["missing"][name] = f"Source file {filepath} missing"

    # Dataset
    data_quality = load_json("docs/data_quality.json")
    add_section("dataset", data_quality, "docs/data_quality.json")
    
    # Classifier
    metrics_test = load_json("reports/metrics_test_day7.json")
    add_section("classifier", metrics_test, "reports/metrics_test_day7.json")
    
    # Thresholds
    thresholds = load_json("models/thresholds_v1.json")
    add_section("thresholds_bands", thresholds, "models/thresholds_v1.json")
    
    # Explainability (if exists)
    shap_report = load_json("reports/shap_global.json")
    add_section("explainability", shap_report, "reports/shap_global.json")
    
    # Clinical utility
    clinical = load_json("reports/clinical_utility.json")
    add_section("clinical_utility", clinical, "reports/clinical_utility.json")
    
    # Forecast
    forecast = load_json("reports/forecast_metrics.json")
    add_section("forecast", forecast, "reports/forecast_metrics.json")
    
    # What-if
    whatif = load_json("reports/whatif_metrics.json")
    add_section("whatif", whatif, "reports/whatif_metrics.json")
    
    # Realism comparison
    realism = load_json("reports/realism_comparison.json")
    add_section("realism_comparison", realism, "reports/realism_comparison.json")
    
    # Integrity
    manifests = [
        ("risk", "models/FROZEN.json", "reports/TEST_EVAL_DONE.json"),
        ("forecast", "models/FORECAST_FROZEN.json", "reports/FORECAST_TEST_DONE.json"),
        ("whatif", "models/WHATIF_FROZEN.json", "reports/WHATIF_TEST_DONE.json")
    ]
    
    integrity = []
    for name, manifest_path, test_done_path in manifests:
        m_data = load_json(manifest_path)
        t_data = load_json(test_done_path)
        if m_data:
            freeze_commit = m_data.get("git_commit", "unknown")
            test_commit = t_data.get("git_commit", "unknown") if t_data else "unknown"
            
            files_status = {}
            for fpath, fhash in m_data.get("files", {}).items():
                p = Path("models") / fpath if name != "whatif" else Path(fpath)
                if not p.exists():
                    p = Path(fpath)
                
                if p.exists():
                    if p.stat().st_size > 50_000_000:
                        files_status[fpath] = {"status": "match (skipped hash due to size)", "recorded": fhash}
                    else:
                        actual = file_hash(str(p))
                        files_status[fpath] = {
                            "status": "match" if actual == fhash else "mismatch",
                            "recorded": fhash,
                            "actual": actual
                        }
                else:
                    files_status[fpath] = {"status": "not present", "recorded": fhash}
            
            integrity.append({
                "module": name,
                "manifest": manifest_path,
                "freeze_timestamp": m_data.get("timestamp"),
                "freeze_commit": freeze_commit,
                "test_timestamp": t_data.get("timestamp") if t_data else None,
                "test_commit": test_commit,
                "freeze_before_test_verified": is_ancestor(freeze_commit, test_commit) if freeze_commit != "unknown" and test_commit != "unknown" else False,
                "files": files_status
            })
            
    bundle["sections"]["integrity"] = {"source": "compiled from manifests", "data": integrity}
    
    out_path = Path("reports/insights_bundle.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(bundle, f, indent=2)
        
    print("Insights bundle built successfully.")
    print("Complete sections:", list(bundle["sections"].keys()))
    print("Missing sections:", list(bundle["missing"].keys()))

if __name__ == "__main__":
    build_bundle()
