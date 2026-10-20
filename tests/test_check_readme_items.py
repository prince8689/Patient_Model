from pathlib import Path
import pytest
from scripts.check_readme_items import check_readme


VALID_SAMPLE_README = """## Project Title
DiaTwin: a Type 2 diabetes digital twin that fuses EHR and wearable data (Happiest Health Digital Twin Challenge 2026)

## Team Details
Prince Maurya (B.Tech, 3rd year). Contact: princemaur7@gmail.com

## College / Incubator Information
Kashi Institute of Technology, Varanasi

## Problem Statement
Glucose monitors report a rise after it has happened.

## Healthcare Use Case
A dashboard for a care team and learning tool.

## Technical Stack
Python, pandas, NumPy, scikit-learn, XGBoost.

## AI/ML Model and Framework Details
XGBoost risk model with causal features. See [LICENSE](LICENSE).

## Demo Video
https://youtu.be/h401ih8xMYA (unlisted YouTube video)

## Open-Source License Details
MIT License (see [LICENSE](LICENSE)).

## Architecture Diagram
[docs/architecture.pdf](docs/architecture.pdf)

## Presentation
[docs/DiaTwin_presentation.pdf](docs/DiaTwin_presentation.pdf) ([PPTX version](docs/DiaTwin_presentation.pptx))

## Public Accessibility
All files and links in this repository are publicly accessible.
"""


def test_valid_sample_readme(tmp_path):
    root = Path(__file__).resolve().parent.parent
    sample = tmp_path / "README_valid.md"
    sample.write_text(VALID_SAMPLE_README, encoding="utf-8")
    assert check_readme(sample, repo_root=root) is True


def test_missing_heading_fails(tmp_path):
    root = Path(__file__).resolve().parent.parent
    bad_content = VALID_SAMPLE_README.replace("## Team Details", "## Something Else")
    sample = tmp_path / "README_bad_heading.md"
    sample.write_text(bad_content, encoding="utf-8")
    assert check_readme(sample, repo_root=root) is False


def test_invalid_video_url_fails(tmp_path):
    root = Path(__file__).resolve().parent.parent
    bad_content = VALID_SAMPLE_README.replace("https://youtu.be/h401ih8xMYA", "https://vimeo.com/123456")
    sample = tmp_path / "README_bad_video.md"
    sample.write_text(bad_content, encoding="utf-8")
    assert check_readme(sample, repo_root=root) is False


def test_missing_diagram_file_fails(tmp_path):
    root = Path(__file__).resolve().parent.parent
    bad_content = VALID_SAMPLE_README.replace("docs/architecture.pdf", "docs/nonexistent_architecture.pdf")
    sample = tmp_path / "README_bad_diagram.md"
    sample.write_text(bad_content, encoding="utf-8")
    assert check_readme(sample, repo_root=root) is False


def test_fill_in_marker_fails(tmp_path):
    root = Path(__file__).resolve().parent.parent
    bad_content = VALID_SAMPLE_README + "\n[TO BE FILLED BY TEAM: details]\n"
    sample = tmp_path / "README_with_marker.md"
    sample.write_text(bad_content, encoding="utf-8")
    assert check_readme(sample, repo_root=root) is False


def test_broken_relative_link_fails(tmp_path):
    root = Path(__file__).resolve().parent.parent
    bad_content = VALID_SAMPLE_README + "\nSee [broken](docs/nonexistent_file.md)\n"
    sample = tmp_path / "README_broken_link.md"
    sample.write_text(bad_content, encoding="utf-8")
    assert check_readme(sample, repo_root=root) is False


def test_actual_readme_passes():
    root = Path(__file__).resolve().parent.parent
    actual_readme = root / "README.md"
    assert check_readme(actual_readme, repo_root=root) is True
