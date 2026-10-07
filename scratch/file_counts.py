from pathlib import Path
root = Path('data/external/shanghai_t2dm')
exts = {}
total = 0
for p in root.rglob('*'):
    if p.is_file():
        total += 1
        exts[p.suffix] = exts.get(p.suffix, 0) + 1
print(f"Total: {total}")
print(f"Extensions: {exts}")
