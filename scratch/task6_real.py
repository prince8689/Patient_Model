
with open('data/external/shanghai_t2dm/MANIFEST.json', 'r') as f:
    print('--- MANIFEST.json ---')
    print(f.read())
    
print('--- Incident Note ---')
print('The real splits file was retired because a review found that the real test split was loaded and a test AUC was reported, which broke the sealing rule. We no longer save real_splits.csv or real_data_seal.json.')

