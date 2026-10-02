from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_starts():
    root = Path(__file__).resolve().parent.parent
    app = AppTest.from_file(str(root / "app" / "main.py"))
    app.run(timeout=10)
    assert not app.exception
    
    # Just verify that the sidebar has the Guided Demo
    assert "Guided Demo Steps" in str(app.sidebar)

def test_safety_wording():
    # Scan all files for forbidden imperative wording
    app_files = list(Path("app").glob("**/*.py")) + list(Path("src/app_lib").glob("**/*.py"))
    
    forbidden = ["you should", "take insulin", "increase your dose", "recommend that you"]
    for fp in app_files:
        content = fp.read_text(encoding="utf-8").lower()
        for f in forbidden:
            assert f not in content, f"Forbidden phrase '{f}' found in {fp}"
