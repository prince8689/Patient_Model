"""Realism computation script.
Delegates to src.real_data.compare to ensure a single committed implementation writes reports/realism_comparison.json.
"""
from src.real_data.compare import compare

def process():
    compare()

if __name__ == "__main__":
    process()
