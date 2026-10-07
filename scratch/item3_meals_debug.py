
import pandas as pd
df = pd.read_csv('data/raw/wearable.csv')
print('Unique meal_carbs_g:', df['meal_carbs_g'].unique())

