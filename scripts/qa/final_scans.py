import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

FORBIDDEN_WORDS = [
    "comprehensive", "robust", "seamless", "rigorous", "strong",
    "state-of-the-art", "production-ready", "perfect", "leverage"
]

FORBIDDEN_PHRASES = [
    "you should", "take insulin", "increase your dose",
    "recommend that you", "we recommend", "clinically validated",
    "proven to", "guarantees",
    "validated against", "real-world", "validated on real"
]

ALLOWLIST_PATTERNS = [
    re.compile(r"not (?:been )?validated on real people", re.IGNORECASE),
    re.compile(r"mimics real-world properties", re.IGNORECASE),
]


def get_project_files():
    out = subprocess.check_output(["git", "ls-files"], cwd=str(ROOT), encoding="utf-8")
    files = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        # Only project files (ignore workflow framework tools)
        if (
            line.startswith(".agent")
            or line.startswith(".agents")
            or line.startswith(".gsd")
            or line.startswith("adapters")
            or line in {"GSD-STYLE.md", "PROJECT_RULES.md", "model_capabilities.yaml"}
        ):
            continue
        files.append(ROOT / line)
    return files


def scan_forbidden_phrases(files):
    issues = []
    text_exts = {".py", ".md", ".txt", ".yaml", ".yml", ".json"}
    for f in files:
        if f.suffix not in text_exts:
            continue
        rel = f.relative_to(ROOT).as_posix()
        # Skip scanner itself and test files checking for forbidden phrases in app output
        if (
            "final_scans.py" in rel
            or "test_insights.py" in rel
            or "clean_docs.py" in rel
            or "find_tone.py" in rel
            or "test_app_smoke.py" in rel
            or "test_whatif_page.py" in rel
            or rel.startswith("scripts/qa/")
        ):
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        for w in FORBIDDEN_WORDS:
            matches = list(re.finditer(r"\b" + re.escape(w) + r"\b", content, re.IGNORECASE))
            for m in matches:
                line_no = content[:m.start()].count("\n") + 1
                issues.append((rel, line_no, f"Forbidden word: '{w}'"))

        for ph in FORBIDDEN_PHRASES:
            matches = list(re.finditer(r"\b" + re.escape(ph) + r"\b", content, re.IGNORECASE))
            for m in matches:
                line_start = content.rfind("\n", 0, m.start()) + 1
                line_end = content.find("\n", m.end())
                if line_end == -1:
                    line_end = len(content)
                line_text = content[line_start:line_end]
                if any(p.search(line_text) for p in ALLOWLIST_PATTERNS):
                    continue
                line_no = content[:m.start()].count("\n") + 1
                issues.append((rel, line_no, f"Forbidden phrase: '{ph}'"))
    return issues


def scan_emojis(files):
    issues = []
    text_exts = {".py", ".md", ".txt", ".yaml", ".yml", ".json"}
    emoji_pattern = re.compile(
        r"[\U00010000-\U0010ffff"
        r"\u2600-\u26ff"
        r"\u2700-\u27bf]"
    )
    for f in files:
        if f.suffix not in text_exts:
            continue
        rel = f.relative_to(ROOT).as_posix()
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        for idx, line in enumerate(content.splitlines(), 1):
            m = emoji_pattern.search(line)
            if m:
                issues.append((rel, idx, f"Emoji character found: {ascii(m.group(0))}"))
    return issues


def scan_absolute_paths(files):
    issues = []
    text_exts = {".py", ".md", ".txt", ".yaml", ".yml", ".json"}
    path_pattern = re.compile(r"(?:[dD]:\\|[cC]:\\Users)", re.IGNORECASE)
    for f in files:
        if f.suffix not in text_exts:
            continue
        rel = f.relative_to(ROOT).as_posix()
        if "final_scans.py" in rel:
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        for idx, line in enumerate(content.splitlines(), 1):
            if path_pattern.search(line):
                issues.append((rel, idx, f"Absolute path found in line: {line.strip()[:60]}"))
    return issues


def scan_day_n(files):
    issues = []
    text_exts = {".py", ".md", ".txt", ".yaml", ".yml", ".json"}
    day_n_pattern = re.compile(r"(?i)\bday\s*\d+\b")
    stage_phase_pattern = re.compile(r"(?i)\b(?:stage|phase)\b")

    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        if day_n_pattern.search(rel):
            issues.append((rel, 0, "Filename contains 'day N'"))
        if stage_phase_pattern.search(rel):
            issues.append((rel, 0, "Filename contains 'stage' or 'phase'"))

        if f.suffix not in text_exts:
            continue
        if (
            "final_scans.py" in rel
            or "clean_docs.py" in rel
            or "protected_files.py" in rel
            or "audit_readme_numbers.py" in rel
        ):
            continue
        # Stored metrics filenames
        if "metrics_test_day7.json" in rel or "test_predictions_day7" in rel or "oof_train_day7" in rel:
            continue

        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        for idx, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            is_heading = stripped.startswith("#")
            is_comment = stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*")

            if f.suffix in {".yaml", ".yml", ".json"}:
                if day_n_pattern.search(line) and "metrics_test_day7" not in line:
                    issues.append((rel, idx, f"Config line contains day N: {line.strip()[:60]}"))
                if stage_phase_pattern.search(line):
                    issues.append((rel, idx, f"Config line contains stage/phase: {line.strip()[:60]}"))
            elif is_heading:
                if day_n_pattern.search(line):
                    issues.append((rel, idx, f"Heading contains day N: {line.strip()[:60]}"))
                if stage_phase_pattern.search(line):
                    issues.append((rel, idx, f"Heading contains stage/phase: {line.strip()[:60]}"))
            elif is_comment:
                if day_n_pattern.search(line) and "metrics_test_day7" not in line:
                    issues.append((rel, idx, f"Comment contains day N: {line.strip()[:60]}"))
                if stage_phase_pattern.search(line):
                    issues.append((rel, idx, f"Comment contains stage/phase: {line.strip()[:60]}"))
    return issues


def scan_file_sizes(files):
    large_files = []
    for f in files:
        if f.exists():
            sz = f.stat().st_size
            if sz > 5 * 1024 * 1024:
                rel = f.relative_to(ROOT).as_posix()
                large_files.append((rel, sz))
    return large_files


def scan_scratch_git():
    out = subprocess.check_output(["git", "ls-files", "scratch"], cwd=str(ROOT), encoding="utf-8")
    return [l.strip() for l in out.splitlines() if l.strip()]


def scan_fenced_code_blocks(files):
    unclosed = []
    md_files = [f for f in files if f.suffix == ".md"]
    for f in md_files:
        rel = f.relative_to(ROOT).as_posix()
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        fence_count = content.count("\x60\x60\x60")
        if fence_count % 2 != 0:
            unclosed.append((rel, fence_count))
    return unclosed


def main():
    files = get_project_files()
    print(f"Total project files scanned: {len(files)}")

    print("\n1. Forbidden Words and Phrases Scan:")
    forbidden_issues = scan_forbidden_phrases(files)
    print(f"   Issues found: {len(forbidden_issues)}")
    for rel, line, desc in forbidden_issues:
        print(f"   - {rel}:{line} {desc}")

    print("\n2. Emoji Scan:")
    emoji_issues = scan_emojis(files)
    print(f"   Issues found: {len(emoji_issues)}")
    for rel, line, desc in emoji_issues:
        print(f"   - {rel}:{line} {desc}")

    print("\n3. Absolute Paths Scan (D:\\ and C:\\Users):")
    path_issues = scan_absolute_paths(files)
    print(f"   Issues found: {len(path_issues)}")
    for rel, line, desc in path_issues:
        print(f"   - {rel}:{line} {desc}")

    print("\n4. 'day N', 'stage', 'phase' Scan (names, comments, headings, config keys):")
    day_issues = scan_day_n(files)
    print(f"   Issues found: {len(day_issues)}")
    for rel, line, desc in day_issues:
        print(f"   - {rel}:{line} {desc}")

    print("\n5. Tracked Files Above 5 MB:")
    large = scan_file_sizes(files)
    print(f"   Files > 5 MB: {len(large)}")
    for rel, sz in large:
        print(f"   - {rel}: {sz / (1024*1024):.2f} MB")

    print("\n6. git ls-files scratch:")
    scratch_files = scan_scratch_git()
    print(f"   Tracked scratch files: {len(scratch_files)}")
    for sf in scratch_files:
        print(f"   - {sf}")

    print("\n7. Closed Fenced Code Blocks in Markdown:")
    unclosed = scan_fenced_code_blocks(files)
    print(f"   Unclosed code blocks: {len(unclosed)}")
    for rel, count in unclosed:
        print(f"   - {rel}: odd count of code fences ({count})")

    all_passed = (
        len(forbidden_issues) == 0 and
        len(emoji_issues) == 0 and
        len(path_issues) == 0 and
        len(day_issues) == 0 and
        len(large) == 0 and
        len(scratch_files) == 0 and
        len(unclosed) == 0
    )
    print(f"\nFinal Scan Result: {'PASS' if all_passed else 'FAIL'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
