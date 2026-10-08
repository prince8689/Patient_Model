import pandas as pd
from pathlib import Path

def check_dups():
    data_dir = Path('data/external/shanghai_t2dm/Shanghai_T2DM')
    all_files = list(data_dir.glob('*.xls*'))
    
    # load all into memory to compare
    dfs = {}
    for f in all_files:
        pat_id = f.stem.split('_')[0]
        df = pd.read_excel(f)
        dfs[pat_id] = df
        
    dups = ['2065', '2068', '2071', '2072']
    for d in dups:
        if d not in dfs: continue
        d_df = dfs[d]
        found_dup = False
        for other, o_df in dfs.items():
            if other == d: continue
            # check if they have the same number of rows and exact same values
            if len(d_df) == len(o_df):
                try:
                    pd.testing.assert_frame_equal(d_df, o_df)
                    print(f"{d} is an EXACT duplicate of {other}!")
                    found_dup = True
                except:
                    pass
        if not found_dup:
            print(f"{d} has no exact duplicates.")

if __name__ == "__main__":
    check_dups()
