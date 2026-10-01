import pytest
from streamlit.testing.v1 import AppTest
from pathlib import Path

def test_app_starts():
    app = AppTest.from_file("app/main.py")
    app.run()
    assert not app.exception
    
    # Check disclaimer in sidebar
    assert "Educational prototype" in str(app.sidebar)

def test_safety_wording():
    # Scan all files for forbidden imperative wording
    import re
    app_files = list(Path("app").glob("**/*.py")) + list(Path("src/app_lib").glob("**/*.py"))
    
    forbidden = ["you should", "take insulin", "increase your dose", "recommend that you"]
    for fp in app_files:
        content = fp.read_text(encoding="utf-8").lower()
        for f in forbidden:
            assert f not in content, f"Forbidden phrase '{f}' found in {fp}"
