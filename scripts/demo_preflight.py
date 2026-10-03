import sys
import os
import json
from pathlib import Path

# Setup sys.path before importing streamlit testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from streamlit.testing.v1 import AppTest

def check_moments():
    reasons = []
    
    # We require P007 at 2026-01-03 21:50
    bundle_path = Path("demo_bundle/states/P007_20260103_2150.json")
    if not bundle_path.exists():
        reasons.append(f"Required demo moment not found in bundle: {bundle_path}")
    else:
        with open(bundle_path, "r") as f:
            data = json.load(f)
            band = data.get("risk", {}).get("band")
            if band not in ["Medium", "High"]:
                reasons.append(f"Expected Medium/High risk for P007 demo moment, found {band}")
                
    return reasons

def check_pages():
    reasons = []
    
    # We set DIATWIN_DEMO_BUNDLE=1 via config instead since os.environ sometimes doesn't reach the app
    # Actually wait, let's just patch config globally for the test process
    import src.utils.config
    orig_load = src.utils.config.load_config
    def patched_load(*args, **kwargs):
        c = orig_load(*args, **kwargs)
        c["app"]["use_demo_bundle"] = True
        return c
    src.utils.config.load_config = patched_load

    try:
        root_dir = Path(__file__).resolve().parent.parent
        pages = [
            root_dir / "app/main.py",
            root_dir / "app/pages/2_Live_Twin.py",
            root_dir / "app/pages/3_What_If_Simulator.py",
            root_dir / "app/pages/4_Model_Insights.py",
            root_dir / "app/pages/5_About.py"
        ]
        
        for p in pages:
            p_str = str(p)
            ptest = AppTest.from_file(str(root_dir / "app/main.py"))
            import pandas as pd
            ptest.session_state["patient_id"] = "P007"
            ptest.session_state["as_of"] = pd.to_datetime("2026-01-03 21:50")
            
            ptest.run()
            
            if "main.py" not in p_str:
                try:
                    ptest.switch_page(p_str)
                    ptest.run()
                except Exception as e:
                    ptest = AppTest.from_file(p_str)
                    ptest.session_state["patient_id"] = "P007"
                    ptest.session_state["as_of"] = pd.to_datetime("2026-01-03 21:50")
                    ptest.run()
            
            if ptest.exception:
                reasons.append(f"Page {p} crashed: {ptest.exception}")
                continue
                
            # Check disclaimer text in markdown or info box
            disclaimer_text = "not a medical device"
            
            found_disclaimer = False
            for md in ptest.markdown:
                if disclaimer_text in md.value.lower():
                    found_disclaimer = True
            for w in ptest.warning:
                if disclaimer_text in w.value.lower():
                    found_disclaimer = True
            for i in ptest.info:
                if disclaimer_text in i.value.lower():
                    found_disclaimer = True
            for c in ptest.caption:
                if disclaimer_text in c.value.lower():
                    found_disclaimer = True
                    
            if not found_disclaimer:
                reasons.append(f"Disclaimer missing or not visible on page {p}")
                
    except Exception as e:
        reasons.append(f"Exception during test runner: {str(e)}")
        
    return reasons

def main():
    print("Running Demo Preflight Checks...")
    
    if not Path("demo_bundle").exists():
        print("NO-GO: demo_bundle directory does not exist.")
        sys.exit(1)
        
    all_reasons = []
    
    print("Checking required demo moments...")
    all_reasons.extend(check_moments())
    
    print("Checking app pages in demo-bundle mode...")
    all_reasons.extend(check_pages())
    
    if all_reasons:
        print("\n=== NO-GO ===")
        print("Preflight failed for the following reasons:")
        for r in all_reasons:
            print(f" - {r}")
        sys.exit(1)
    else:
        print("\n=== GO ===")
        print("All pages render successfully and demo moments are verified.")
        sys.exit(0)

if __name__ == "__main__":
    main()
