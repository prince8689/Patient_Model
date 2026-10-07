
import pandas as pd
from pathlib import Path
f = Path('data/external/shanghai_t2dm/Shanghai_T2DM/2000_0_20201230.xlsx')
df = pd.read_excel(f)
print(df['Date'].head(10))
print(df['Date'].diff().head(10))

