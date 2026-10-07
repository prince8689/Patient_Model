import pandas as pd
df = pd.read_csv('data/processed/real_profiles.csv')

try:
    splits = pd.read_csv('data/processed/real_splits.csv')
    df = df.merge(splits, on='patient_id', how='left')
except FileNotFoundError:
    print("real_splits.csv not found")

df['true_patient_id'] = df['patient_id'].apply(lambda x: str(x).split('_')[0])
df['recording_id'] = df['patient_id']

n_pat = df['true_patient_id'].nunique()
n_rec = df['recording_id'].nunique()
print(f'Unique patients: {n_pat}')
print(f'Unique recordings: {n_rec}')

multi = df.groupby('true_patient_id')['recording_id'].count()
multi_pats = multi[multi > 1].index.tolist()
for p in multi_pats:
    recs = df[df['true_patient_id'] == p]
    print(f'Patient {p}:')
    for _, row in recs.iterrows():
        split = row.get("split", "unknown")
        print(f'  Recording {row["recording_id"]} fell into split: {split}')
