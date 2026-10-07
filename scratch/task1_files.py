
from pathlib import Path
from collections import defaultdict
root = Path('data/external/shanghai_t2dm')
counts = defaultdict(int)
files = list(root.rglob('*'))
for f in files:
    if f.is_file():
        ext = f.suffix
        folder = f.parent.name
        counts[f'{folder}/*{ext}'] += 1
print('File counts:')
for k, v in counts.items():
    print(f'{k}: {v}')

