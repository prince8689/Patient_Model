
import pandas as pd
df = pd.read_csv('data/raw/wearable.csv', nrows=5)
print(df.columns.tolist())

