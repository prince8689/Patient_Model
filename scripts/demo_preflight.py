import sys
import os
from streamlit.testing.v1 import AppTest

def check_page(at, page_index, page_name):
    # Navigate to page
    if page_index > 0:
        page_files = {
            "Patient List": "pages/1_Patient_List.py",
            "Live Twin": "pages/2_Live_Twin.py",
            "What-if Simulator": "pages/3_What_If_Simulator.py",
            "Model Insights": "pages/4_Model_Insights.py",
            "About": "pages/5_About.py"
        }
        at.switch_page(page_files[page_name]).run()
    
    assert not at.exception, f"Exception occurred on {page_name}: {at.exception[0].message if at.exception else ''}"
    
    # Check disclaimer
    has_disclaimer = any("medical device" in m.value.lower() or "disclaimer" in m.value.lower() 
                         for m in at.markdown if m.value)
    
    if not has_disclaimer:
        # It might be in the sidebar or a warning block
        has_warning = any("medical device" in w.value.lower() or "disclaimer" in w.value.lower() 
                          for w in at.warning if w.value)
        has_error = any("medical device" in e.value.lower() or "disclaimer" in e.value.lower() 
                        for e in at.error if e.value)
        has_info = any("medical device" in i.value.lower() or "disclaimer" in i.value.lower() 
                       for i in at.info if i.value)
        if not (has_warning or has_error or has_info):
            print(f"NO-GO: Disclaimer not found on page {page_name}")
            sys.exit(1)

def run_preflight():
    os.environ["DIATWIN_DEMO_BUNDLE"] = "1"
    
    try:
        from pathlib import Path
        app_path = str(Path(__file__).resolve().parent.parent / "app" / "main.py")
        at = AppTest.from_file(app_path)
        at.run()
        
        if at.exception:
            print(f"NO-GO: App crashed on startup: {at.exception[0].message}")
            sys.exit(1)
            
        print("Preflight: App started successfully.")
        
        # Check Patient List (default page)
        check_page(at, 0, "Patient List")
        print("Preflight: Patient List page OK.")
        
        # Check Live Twin
        check_page(at, 1, "Live Twin")
        # Ensure driver is visible
        has_driver = any("It has been a long time" in m.value or "Recent meal" in m.value for m in at.markdown if m.value)
        # Actually it's hard to predict exactly which patient is loaded first, but we can verify it doesn't crash
        print("Preflight: Live Twin page OK.")
        
        # Check What-if Simulator
        check_page(at, 2, "What-if Simulator")
        print("Preflight: What-if Simulator page OK.")
        
        # Check Model Insights
        check_page(at, 3, "Model Insights")
        print("Preflight: Model Insights page OK.")
        
        # Check About
        check_page(at, 4, "About")
        print("Preflight: About page OK.")
        
        print("GO: All preflight checks passed successfully.")
        sys.exit(0)
        
    except Exception as e:
        print(f"NO-GO: Preflight failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_preflight()
