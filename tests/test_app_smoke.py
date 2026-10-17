from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_starts():
    root = Path(__file__).resolve().parent.parent
    app = AppTest.from_file(str(root / "app" / "main.py"), default_timeout=60)
    app.run()
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


def test_requirements_identical():
    root = Path(__file__).resolve().parent.parent
    demo_req = (root / "requirements-demo.txt").read_text(encoding="utf-8")
    app_req = (root / "app" / "requirements.txt").read_text(encoding="utf-8")
    assert app_req == demo_req, "app/requirements.txt must be identical to requirements-demo.txt"
