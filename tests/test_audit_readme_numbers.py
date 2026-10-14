import pytest
from scripts.audit_readme_numbers import run_audit


def test_readme_and_docs_numbers_audit():
    passed, n_match, n_mismatch, n_nosrc = run_audit()
    assert n_mismatch == 0, f"Found {n_mismatch} numerical mismatches in README and documentation files!"
    assert passed is True
