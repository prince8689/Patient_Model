
import pandas as pd
gluc_df = pd.read_csv('data/processed/real_glucose.csv')
pids = gluc_df['patient_id'].nunique()
print(f'Patients remaining after harmonize: {pids}')

