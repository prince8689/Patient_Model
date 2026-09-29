import sys

def verify_setup():
    print(f"Python version: {sys.version}")
    assert sys.version_info >= (3, 10), "Python version must be >= 3.10"
    
    packages = [
        "pandas",
        "numpy",
        "sklearn",
        "xgboost",
        "shap",
        "streamlit",
        "plotly",
        "matplotlib",
        "pytest",
        "joblib",
        "yaml"
    ]
    
    for pkg in packages:
        try:
            mod = __import__(pkg)
            version = getattr(mod, '__version__', 'unknown')
            print(f"Successfully imported {pkg} (version: {version})")
        except ImportError as e:
            print(f"Failed to import {pkg}: {e}")
            sys.exit(1)
            
    print("SETUP OK")

if __name__ == "__main__":
    verify_setup()
