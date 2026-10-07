import pandas as pd
from pathlib import Path
import json

root = Path('data/external/shanghai_t2dm')
data_folder = root / "Shanghai_T2DM"
summary_file = root / "Shanghai_T2DM_Summary.xlsx"

summary_df = pd.read_excel(summary_file, sheet_name="T2DM")
profile_pids = set()
for _, row in summary_df.iterrows():
    rec_id = str(row['Patient Number'])
    pid = rec_id.split('_')[0]
    profile_pids.add(pid)

cgm_files = list(data_folder.glob("*.xls*"))
cgm_pids = set()
cgm_recs = set()
cgm_recs_list = []
for f in cgm_files:
    if f.name.startswith("._"):
        continue
    rec_id = f.stem
    pid = rec_id.split('_')[0]
    cgm_pids.add(pid)
    cgm_recs.add(rec_id)
    cgm_recs_list.append(pid)

overlap = profile_pids.intersection(cgm_pids)
missing_cgm = profile_pids - cgm_pids
missing_profile = cgm_pids - profile_pids
from collections import Counter
counts = Counter(cgm_recs_list)
multi_rec = [pid for pid, c in counts.items() if c > 1]

print(f"Profile PIDs: {len(profile_pids)}")
print(f"CGM PIDs: {len(cgm_pids)}")
print(f"Overlap: {len(overlap)}")
print(f"Patients without CGM: {missing_cgm}")
print(f"Recordings without profile: {missing_profile}")
print(f"Patients with multiple recordings: {multi_rec}")

