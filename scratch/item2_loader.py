
from src.data_gen.loader import _ShanghaiT2DMLoader
import pandas as pd

loader = _ShanghaiT2DMLoader()
cgm_files, skips = loader._find_cgm_files()
print(f'CGM files opened: {len(cgm_files)}')
print('Skips:')
for f, reason in skips.items():
    print(f'  {f}: {reason}')

