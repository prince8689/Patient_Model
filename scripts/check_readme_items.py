#!/usr/bin/env python3
"""Validation checker for README.md submission requirements.

Validates:
1. Presence of 12 required competition sections under their own headings.
2. Demo video URL is a valid youtube.com or youtu.be link.
3. Architecture diagram and Presentation sections link to existing .pdf or .pptx files in the repo.
4. No fill-in markers or placeholders remain.
5. All relative links and image paths point to existing files tracked in git.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


REQUIRED_HEADINGS = [
    ("Team details", r"#+\s+Team Details"),
    ("College / Incubator information", r"#+\s+College\s*(?:/|and)?\s*Incubator Information"),
    ("Project title", r"#+\s+Project Title"),
    ("Problem statement", r"#+\s+Problem Statement"),
    ("Healthcare use case", r"#+\s+Healthcare Use Case"),
    ("Technical stack", r"#+\s+Technical Stack"),
    ("AI/ML model and framework details", r"#+\s+AI/ML Model and Framework Details"),
    ("Demo video", r"#+\s+Demo Video"),
    ("Open-source license details", r"#+\s+Open-Source License Details"),
    ("Architecture diagram", r"#+\s+Architecture Diagram"),
    ("Presentation", r"#+\s+Presentation"),
    ("Public accessibility", r"#+\s+Public Accessibility"),
]

FILL_IN_PATTERNS = [
    r"\[LIVE DEMO URL\]",
    r"\[VIDEO URL\]",
    r"\[TO BE FILLED",
    r"\[Team name\]",
    r"\[YOUTUBE UNLISTED LINK\]",
    r"\[YOUR EMAIL\]",
    r"<YOUR EMAIL>",
    r"\[INSERT ",
]


def get_git_tracked_files(repo_root: Path):
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        return set(line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip())
    except Exception:
        return None


def parse_sections(content: str):
    sections = {}
    lines = content.splitlines()
    current_heading = None
    current_content = []

    for line in lines:
        if line.startswith("#"):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_content).strip()
            current_heading = line.strip()
            current_content = []
        else:
            if current_heading is not None:
                current_content.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_content).strip()

    return sections


def check_readme(readme_path: Path, repo_root: Path = None):
    if repo_root is None:
        repo_root = readme_path.parent

    if not readme_path.is_file():
        print(f"FAIL: File not found: {readme_path}")
        return False

    content = readme_path.read_text(encoding="utf-8")
    sections = parse_sections(content)
    tracked_files = get_git_tracked_files(repo_root)

    results = []
    overall_pass = True

    # 1. Check each of the 12 required headings and contents
    for name, pattern in REQUIRED_HEADINGS:
        matching_heading = None
        for heading in sections:
            if re.search(pattern, heading, re.IGNORECASE):
                matching_heading = heading
                break

        if not matching_heading:
            results.append((f"Section: {name}", False, f"Heading matching '{pattern}' not found"))
            overall_pass = False
            continue

        section_body = sections[matching_heading]
        if not section_body:
            results.append((f"Section: {name}", False, "Section heading found but content is empty"))
            overall_pass = False
            continue

        # Specific content validation
        if name == "Demo video":
            yt_match = re.search(r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-]+)", section_body)
            if yt_match:
                results.append((f"Section: {name}", True, f"Found valid video URL: {yt_match.group(0)}"))
            else:
                results.append((f"Section: {name}", False, "Missing valid youtube.com or youtu.be URL"))
                overall_pass = False

        elif name == "Architecture diagram":
            file_match = re.findall(r"\[([^\]]+)\]\(([^)]+\.(?:pdf|pptx))\)", section_body, re.IGNORECASE)
            if not file_match:
                # also check for direct path mention
                file_match_direct = re.findall(r"(docs/[\w\.-]+\.(?:pdf|pptx))", section_body, re.IGNORECASE)
                candidates = file_match_direct
            else:
                candidates = [target for _, target in file_match]

            found_valid = False
            for cand in candidates:
                cand_path = (repo_root / cand).resolve()
                if cand_path.is_file():
                    found_valid = True
                    break

            if found_valid:
                results.append((f"Section: {name}", True, f"Found existing diagram file link: {candidates}"))
            else:
                results.append((f"Section: {name}", False, f"No existing .pdf/.pptx file linked in section: {candidates}"))
                overall_pass = False

        elif name == "Presentation":
            file_match = re.findall(r"\[([^\]]+)\]\(([^)]+\.(?:pdf|pptx))\)", section_body, re.IGNORECASE)
            if not file_match:
                file_match_direct = re.findall(r"(docs/[\w\.-]+\.(?:pdf|pptx))", section_body, re.IGNORECASE)
                candidates = file_match_direct
            else:
                candidates = [target for _, target in file_match]

            found_valid = False
            for cand in candidates:
                cand_path = (repo_root / cand).resolve()
                if cand_path.is_file():
                    found_valid = True
                    break

            if found_valid:
                results.append((f"Section: {name}", True, f"Found existing presentation file link: {candidates}"))
            else:
                results.append((f"Section: {name}", False, f"No existing .pdf/.pptx file linked in section: {candidates}"))
                overall_pass = False

        else:
            results.append((f"Section: {name}", True, f"Present ({len(section_body.splitlines())} lines)"))

    # 2. Check for fill-in markers
    markers_found = []
    for pat in FILL_IN_PATTERNS:
        matches = re.findall(pat, content, re.IGNORECASE)
        if matches:
            markers_found.extend(matches)

    if markers_found:
        results.append(("Fill-in markers check", False, f"Found markers: {set(markers_found)}"))
        overall_pass = False
    else:
        results.append(("Fill-in markers check", True, "No fill-in markers or placeholders found"))

    # 3. Check all relative links and image paths in README
    all_links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", content)
    broken_links = []
    untracked_links = []

    for text, target in all_links:
        # Ignore external links and anchors
        target_clean = target.split("#")[0].strip()
        if not target_clean:
            continue
        if target_clean.startswith("http://") or target_clean.startswith("https://") or target_clean.startswith("mailto:"):
            continue

        target_path = (repo_root / target_clean).resolve()
        if not target_path.exists():
            broken_links.append(target_clean)
        elif tracked_files is not None:
            rel_path = os.path.relpath(target_path, repo_root).replace("\\", "/")
            if rel_path not in tracked_files:
                untracked_links.append(rel_path)

    if broken_links:
        results.append(("Relative link existence", False, f"Broken relative links: {broken_links}"))
        overall_pass = False
    else:
        results.append(("Relative link existence", True, "All relative links point to existing files"))

    if untracked_links:
        results.append(("Relative link git tracking", False, f"Files exist but are not tracked in git: {untracked_links}"))
        overall_pass = False
    else:
        results.append(("Relative link git tracking", True, "All linked relative files are tracked in git"))

    # Print results
    print("==================================================")
    print("README Requirements and Integrity Check Results")
    print("==================================================")
    for check_name, status, details in results:
        status_str = "PASS" if status else "FAIL"
        print(f"[{status_str}] {check_name}: {details}")

    print("--------------------------------------------------")
    print(f"Overall README Item Check: {'PASS' if overall_pass else 'FAIL'}")
    print("==================================================")

    return overall_pass


def main():
    parser = argparse.ArgumentParser(description="Check README.md sections and links.")
    parser.add_argument("readme", nargs="?", default="README.md", help="Path to README.md")
    parser.add_argument("--repo-root", default=None, help="Root path of the repository")
    args = parser.parse_args()

    readme_path = Path(args.readme).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else readme_path.parent

    success = check_readme(readme_path, repo_root)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
