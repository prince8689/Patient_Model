
import shutil
import os

with open('LICENSE', 'r') as f:
    mit_license = f.read()

prov = f'''# DiaTwin Project Provenance

## Data Sources
The real dataset used in this project is ShanghaiT2DM (Citation: Zhao et al., Scientific Data 10, 35, 2023, DOI: 10.6084/m9.figshare.c.6310860).

## Data License
The dataset is available under the CC BY 4.0 license: https://creativecommons.org/licenses/by/4.0/ (as printed on the download page).

## Code License
`	ext
{mit_license}
`

## Raw Data Repository Policy
The raw dataset is not distributed in the repository to maintain repository hygiene and due to the large size of the files.
'''
with open('docs/PROVENANCE.md', 'w') as f:
    f.write(prov)

if os.path.exists('docs/INVENTORY.md'):
    os.remove('docs/INVENTORY.md')

