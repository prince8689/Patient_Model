from pathlib import Path
import pytest
from scripts.audit_readme_numbers import audit_file, load_all_json_sources, run_audit


def test_readme_and_docs_numbers_audit():
    passed, n_match, n_mismatch, n_nosrc = run_audit()
    assert n_mismatch == 0, f"Found {n_mismatch} numerical mismatches in README and documentation files!"
    assert n_nosrc == 0, f"Found {n_nosrc} unsourced numbers in README and documentation files!"
    assert passed is True


def test_urls_and_link_targets_with_digits_are_ignored(tmp_path):
    root = Path(__file__).resolve().parent.parent
    sample_file = tmp_path / "sample_test_doc.md"
    sample_file.write_text(
        "Link to youtube: https://youtu.be/h401ih8xMYA\n"
        "Link to doc: [Presentation](docs/presentation_v2.pdf)\n"
        "Contact email: princemaur7@gmail.com\n",
        encoding="utf-8",
    )
    sources = load_all_json_sources(root)
    results = audit_file(sample_file, root, sources)
    # None of the digits 401, 8, 2, or 7 from URLs, targets, or emails should be flagged
    no_source = [r for r in results if r["status"] == "NO SOURCE"]
    mismatch = [r for r in results if r["status"] == "MISMATCH"]
    assert len(no_source) == 0, f"Expected 0 NO SOURCE, got: {no_source}"
    assert len(mismatch) == 0, f"Expected 0 MISMATCH, got: {mismatch}"
