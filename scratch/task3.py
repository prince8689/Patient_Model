
import pandas as pd
from pathlib import Path
cgm_files = list(Path('data/external/shanghai_t2dm/Shanghai_T2DM').glob('*.xls*'))
cgm_recs = [f.stem for f in cgm_files]
cgm_pids = set([rec.split('_')[0] for rec in cgm_recs])

summary_df = pd.read_excel('data/external/shanghai_t2dm/Shanghai_T2DM_Summary.xlsx', sheet_name='T2DM')
prof_recs = [str(r) for r in summary_df['Patient Number'].dropna().tolist()]
prof_pids = set([rec.split('_')[0] for rec in prof_recs])

overlap_pids = cgm_pids.intersection(prof_pids)

print(f'Unique PIDs in CGM files: {len(cgm_pids)}')
print(f'Unique PIDs in profile: {len(prof_pids)}')
print(f'Overlap PIDs: {len(overlap_pids)}')

no_cgm = prof_pids - cgm_pids
print(f'Patients without CGM: {list(no_cgm)}')

no_prof = cgm_pids - prof_pids
print(f'Patients without Profile: {list(no_prof)}')

pid_counts = {}
for rec in cgm_recs:
    pid = rec.split('_')[0]
    pid_counts[pid] = pid_counts.get(pid, 0) + 1

multiple = sum(1 for v in pid_counts.values() if v > 1)
print(f'Patients with >1 recording: {multiple}')

