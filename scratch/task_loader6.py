
import pandas as pd
from pathlib import Path
import os

raw_dir = Path('data/external/shanghai_t2dm')
data_folder = raw_dir / 'Shanghai_T2DM'

files = list(data_folder.glob('*.xls*'))
print(f'Total files found: {len(files)}')

