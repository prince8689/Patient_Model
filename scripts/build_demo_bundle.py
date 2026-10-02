import shutil
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.app_lib.data_access import (
    get_demo_patients,
    get_patient_timeline,
    get_patient_wearable,
    get_patients_df,
)
from src.app_lib.moments import default_moment
from src.app_lib.viewmodels import export_state_json
from src.utils.config import load_config


def build_bundle():
    config = load_config()
    bundle_dir = Path("demo_bundle")
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
        
    bundle_dir.mkdir()
    (bundle_dir / "timelines").mkdir()
    (bundle_dir / "wearable").mkdir()
    (bundle_dir / "states").mkdir()
    
    pids = get_demo_patients()
    
    # Patients df
    pdf = get_patients_df()
    demo_pdf = pdf[pdf["patient_id"].isin(pids)].copy()
    
    # STRICT RULE: No hidden truth in demo bundle
    forbidden_cols = ["archetype", "baseline_insulin_sensitivity"]
    for c in forbidden_cols:
        if c in demo_pdf.columns:
            demo_pdf = demo_pdf.drop(columns=[c])
            
    demo_pdf.to_csv(bundle_dir / "patients.csv", index=False)
    
    # Process each patient
    for pid in pids:
        print(f"Processing {pid}...")
        # Timeline
        tl = get_patient_timeline(pid)
        tl.to_parquet(bundle_dir / "timelines" / f"{pid}.parquet")
        print(f"  Timeline generated for {pid}")
        
        # Wearable (remove labels/future truth if any)
        w = get_patient_wearable(pid)
        for c in ["label", "spike_next_2h", "sim_params"]:
            if c in w.columns:
                w = w.drop(columns=[c])
        w.to_parquet(bundle_dir / "wearable" / f"{pid}.parquet")
        print(f"  Wearable data saved for {pid}")
        
        # Default moment state
        mom = default_moment(pid)
        print(f"  Exporting state json for {pid} at {mom}...")
        state_json = export_state_json(pid, mom)
        state_file = bundle_dir / "states" / f"{pid}_{mom.strftime('%Y%m%d_%H%M')}.json"
        with open(state_file, "w") as f:
            f.write(state_json)
        print(f"  State JSON exported for {pid}")
            
    # Calculate bundle size
    total_size = sum(f.stat().st_size for f in bundle_dir.rglob('*') if f.is_file())
    print(f"Demo bundle built successfully. Total size: {total_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    build_bundle()
