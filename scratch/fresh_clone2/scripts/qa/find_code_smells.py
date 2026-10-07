import os
import re
from pathlib import Path


def scan_files():
    root = Path(__file__).resolve().parent.parent.parent
    targets = [root / "src", root / "app", root / "scripts", root / "tests"]
    
    findings = {
        "todo": [],
        "print": [],
        "bare_except": [],
        "commented_code": []
    }
    
    todo_re = re.compile(r'(?i)#\s*(TODO|FIXME|XXX)')
    print_re = re.compile(r'\bprint\(')
    bare_except_re = re.compile(r'except\s*:')
    
    for t in targets:
        for path, _, files in os.walk(t):
            for f in files:
                if not f.endswith(".py"):
                    continue
                full_path = Path(path) / f
                
                try:
                    with open(full_path, "r", encoding="utf-8") as file:
                        for i, line in enumerate(file, 1):
                            if todo_re.search(line):
                                findings["todo"].append(f"{full_path.relative_to(root)}:{i} {line.strip()}")
                            if print_re.search(line) and "scripts" not in str(full_path):
                                findings["print"].append(f"{full_path.relative_to(root)}:{i} {line.strip()}")
                            if bare_except_re.search(line):
                                findings["bare_except"].append(f"{full_path.relative_to(root)}:{i} {line.strip()}")
                except Exception:
                    pass
    return findings

if __name__ == "__main__":
    import pprint
    pprint.pprint(scan_files())
