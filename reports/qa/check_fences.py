import re
from pathlib import Path

files = ['docs/PROVENANCE.md', 'docs/REAL_DATA.md', 'README.md']
open_fences = False

for file in files:
    path = Path(file)
    if not path.exists():
        continue
    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    in_fence = False
    fence_type = ""
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            if not in_fence:
                in_fence = True
                fence_type = line.strip()
            else:
                in_fence = False
    
    if in_fence:
        print(f"Error: {file} has an unclosed code fence starting with {fence_type}")
        open_fences = True
    else:
        print(f"{file}: All fences closed.")

if open_fences:
    exit(1)
