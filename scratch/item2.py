
import os
from collections import Counter
from pathlib import Path

root = Path('data/external/shanghai_t2dm')
counts = Counter()
for path in root.rglob('*'):
    if path.is_file():
        ext = path.suffix.lower()
        counts[f'{path.parent.name}/{ext}'] += 1

print('File count under data/external/shanghai_t2dm:')
for k, v in sorted(counts.items()):
    print(f'{k}: {v}')

