import os
import re
from pathlib import Path

def find_words():
    root = Path(__file__).resolve().parent.parent.parent
    tone_words = ["comprehensive", "robust", "seamless", "seamlessly", "cutting-edge", "state-of-the-art", "leverage", "delve", "holistic", "powerful", "revolutionary", "game-changing", "unlock", "empower"]
    
    regex = re.compile(r"\b(" + "|".join(tone_words) + r")\b", flags=re.IGNORECASE)
    
    hits = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        if ".git" in rel_dir.parts or ".venv" in rel_dir.parts or "models" in rel_dir.parts or "reports" in rel_dir.parts or "configs" in rel_dir.parts or "data" in rel_dir.parts:
            continue
            
        for f in filenames:
            if not f.endswith((".py", ".md", ".txt", ".sh", "Makefile", ".yml", ".yaml")):
                continue
                
            f_path = root / rel_dir / f
            try:
                lines = f_path.read_text(encoding="utf-8").splitlines()
                for i, line in enumerate(lines):
                    if regex.search(line):
                        hits.append(f"{rel_dir / f}:{i+1}: {line}")
            except Exception:
                pass
                
    for h in hits:
        print(h)

if __name__ == "__main__":
    find_words()
