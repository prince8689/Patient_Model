
import json
import sys
from pathlib import Path
root = Path('.').resolve()
sys.path.insert(0, str(root))
from src.utils.config import load_config
config = load_config(root / 'configs/config.yaml')
from src.twin.loader import TwinRegistry
registry = TwinRegistry(config)
t2 = registry.register('P001')
from src.twin.replay import StreamReplayer
r2 = StreamReplayer(str(root / 'data' / 'raw' / 'wearable.csv'), 'P001')
for i, sample in enumerate(r2.stream()):
    t2.ingest(sample)
    if i > 100: break
state2 = t2.get_state()
snap = t2.snapshot()

registry3 = TwinRegistry(config)
from src.twin.loader import load_frozen_artifacts
artifacts = load_frozen_artifacts(config)
t3 = registry3.register('P001')
t3 = t3.restore(snap, pipeline=artifacts[0], calibrator=artifacts[1], thresholds=artifacts[2], config=config, explainer=None)
state3 = t3.get_state()

d2 = state2.to_dict()
d3 = state3.to_dict()

def find_diff(d1, d2, path=''):
    if isinstance(d1, dict):
        for k in d1:
            if k not in d2:
                print(f'{path}.{k} missing in d2')
            else:
                find_diff(d1[k], d2[k], f'{path}.{k}')
    elif isinstance(d1, list):
        if len(d1) != len(d2):
            print(f'{path} length diff {len(d1)} != {len(d2)}')
        for i, (v1, v2) in enumerate(zip(d1, d2)):
            find_diff(v1, v2, f'{path}[{i}]')
    else:
        if d1 != d2:
            print(f'{path}: {d1} != {d2}')

find_diff(d2, d3)

