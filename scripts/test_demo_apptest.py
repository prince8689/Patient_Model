import os
import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

os.environ["DIATWIN_DEMO_BUNDLE"] = "1"

root = Path(__file__).resolve().parent.parent

pages = [
    ("Main Entry", root / "app" / "main.py"),
    ("1_Patient_List", root / "app" / "pages" / "1_Patient_List.py"),
    ("2_Live_Twin", root / "app" / "pages" / "2_Live_Twin.py"),
    ("3_What_If_Simulator", root / "app" / "pages" / "3_What_If_Simulator.py"),
    ("4_Model_Insights", root / "app" / "pages" / "4_Model_Insights.py"),
    ("5_About", root / "app" / "pages" / "5_About.py"),
    ("User Data Entry", root / "app" / "pages" / "user_data_entry.py"),
]

print("=== AppTest in clean demo_env with DIATWIN_DEMO_BUNDLE=1 ===")
all_pass = True
for name, p in pages:
    try:
        app = AppTest.from_file(str(p), default_timeout=60)
        app.run()
        if app.exception:
            print(f"Page '{name}': FAIL")
            for exc in app.exception:
                print(f"  Exception: {exc}")
            all_pass = False
        else:
            print(f"Page '{name}': PASS")
    except Exception as e:
        print(f"Page '{name}': ERROR ({e})")
        all_pass = False

print("\nAppTest overall result:", "PASS" if all_pass else "FAIL")
