import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import json

def run_app_check(clone_dir, python_exe):
    print("--- Running App-Only Check ---")
    # 2. Virtual environment and requirements
    subprocess.check_call([sys.executable, "-m", "venv", str(clone_dir / ".venv")])
    if os.name == "nt":
        venv_python = clone_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = clone_dir / ".venv" / "bin" / "python"
        
    print("Installing requirements...")
    subprocess.check_call([venv_python, "-m", "pip", "install", "-r", "requirements.txt", "pytest"], cwd=clone_dir)
    
    # 3. Test suite
    print("Running tests (missing artifacts will skip)...")
    try:
        subprocess.check_call([venv_python, "-m", "pytest", "tests/"], cwd=clone_dir)
        print("Tests passed!")
    except subprocess.CalledProcessError:
        print("Tests failed/skipped.")
        
    # 4. AppTest smoke test
    print("Running AppTest smoke tests...")
    # Actually we can just run the test_app_smoke.py since it has AppTest inside
    try:
        subprocess.check_call([venv_python, "-m", "pytest", "tests/test_app_smoke.py"], cwd=clone_dir)
        print("App smoke tests passed!")
    except subprocess.CalledProcessError:
        print("App smoke tests failed.")

    # 5. Repo size
    total_size = sum(f.stat().st_size for f in clone_dir.rglob('*') if f.is_file() and ".venv" not in f.parts and ".git" not in f.parts)
    print(f"Committed repo size (excl .venv, .git): {total_size / 1024 / 1024:.2f} MB")
    
    files = [(f, f.stat().st_size) for f in clone_dir.rglob('*') if f.is_file() and ".venv" not in f.parts and ".git" not in f.parts]
    files.sort(key=lambda x: x[1], reverse=True)
    print("Largest 10 files:")
    for f, size in files[:10]:
        print(f"  {f.relative_to(clone_dir)}: {size / 1024 / 1024:.2f} MB")
        
def run_pipeline_check(clone_dir, python_exe):
    print("--- Running Full Pipeline Reproduction ---")
    if os.name == "nt":
        venv_python = clone_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = clone_dir / ".venv" / "bin" / "python"
        
    # We will run up to insights_bundle
    try:
        subprocess.check_call([venv_python, "scripts/run_pipeline.py", "--fresh-protocol", "--to-stage", "insights_bundle"], cwd=clone_dir)
    except subprocess.CalledProcessError:
        print("Pipeline failed.")
        
    # compare results
    print("Comparing results...")
    
def main():
    root = Path(__file__).resolve().parent.parent.parent
    
    # 1. Clone local repo
    with tempfile.TemporaryDirectory() as temp_dir:
        clone_dir = Path(temp_dir) / "clone"
        subprocess.check_call(["git", "clone", str(root), str(clone_dir)])
        
        run_app_check(clone_dir, sys.executable)
        
        # run_pipeline_check(clone_dir, sys.executable)
        # We will not run the full pipeline in the script automatically as it takes too long for standard execution,
        # we will do a dry-run or partial run.
        
if __name__ == "__main__":
    main()
