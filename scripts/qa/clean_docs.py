import re
from pathlib import Path

def clean_file(filepath):
    content = filepath.read_text(encoding="utf-8")
    
    # 1. Remove (Day X) or Day X references
    # For SPEC.md specifically, there are lines like "Status: Day X complete" or "## 16. Twin Engine Architecture (Day 8)"
    content = re.sub(r"(?i)\(?\bDay\s+\d+\)?", "", content)
    content = re.sub(r"(?i)\(?\bStep\s+\d+\)?", "", content)
    
    # 2. Fix multiple spaces and empty parens left over
    content = content.replace("()", "")
    content = re.sub(r" {2,}", " ", content)
    
    # 3. Rename Assumptions section to plain language if needed
    content = content.replace("## 19. Assumptions", "## Project Decisions and Assumptions")
    
    # 4. Remove tone words
    tone_words = ["comprehensive", "robust", "seamless", "seamlessly", "cutting-edge", "state-of-the-art", "leverage", "delve", "holistic", "powerful", "revolutionary", "game-changing", "unlock", "empower", "in today's world", "it is important to note", "in conclusion", "moreover", "furthermore", "additionally"]
    
    for w in tone_words:
        # Case insensitive word replace
        pattern = re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE)
        content = pattern.sub("", content)
        
    filepath.write_text(content, encoding="utf-8")

root = Path(__file__).resolve().parent.parent.parent
docs = ["DASHBOARD.md", "FORECAST.md", "INTEGRITY.md", "QA_REPORT.md", "SPEC.md"]
for d in docs:
    p = root / "docs" / d
    if p.exists():
        clean_file(p)
