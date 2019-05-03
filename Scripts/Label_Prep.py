# CPTAC Images Join
import pandas as pd
import numpy as np

imglist = pd.read_csv('CPTAC-LUAD-HEslide-filename-mapping_Jan2019.csv', header=0)

samplelist = pd.read_csv('CPTAC_LUAD.csv', header=0)

imglist = imglist[['Slide_ID', 'FileName']]

samplelist = samplelist.join(imglist.set_index('Slide_ID'), how='inner', on='Slide_ID')

samplelist = samplelist.dropna(subset=['FileName'])

samplelist = samplelist[['Case_ID', 'Slide_ID', 'FileName']]

Labelfile = pd.read_csv('luad-v2.0-sample-annotation.csv', header=0)

Labelfile = Labelfile.loc[Labelfile['Type'] == 'Tumor']

Labelfile = Labelfile[['Participant', 'STK11.mutation.status']]

Labelfile = Labelfile.rename(columns={'Participant': 'Case_ID', 'STK11.mutation.status': 'STK11'})

Labelfile = Labelfile.join(samplelist.set_index('Case_ID'), how='inner', on='Case_ID')

Labelfile = Labelfile.drop('Case_ID', axis=1)

Labelfile = Labelfile.drop_duplicates()

Labelfile.to_csv('CPTAC_Joint.csv', index=False, header=True)

# TCGA

import pandas as pd
import os
# Get all images in the root directory
def image_ids_in(root_dir, ignore=['.DS_Store', 'dict.csv']):
    ids = []
    for id in os.listdir(root_dir):
        if id in ignore:
            print('Skipping ID:', id)
        else:
            dirname = id.split('-01Z')[0]
            ids.append([id, dirname])
    return ids

TCGAls = image_ids_in('../images/TCGA')
TCGAls = pd.DataFrame(TCGAls)
TCGAls = TCGAls.rename(columns={'0': 'FileName', '1': 'Slide_ID'})
TCGAls.to_csv('../TCGAls.csv', index=False, header=True)


import pandas as pd
import os
TCGAall = pd.read_csv('TCGA_all.tsv', sep='\t', header=0)
TCGAstk = pd.read_csv('TCGA_STK11_MUT.tsv', sep='\t', header=0)
TCGAim = pd.read_csv('TCGAls.csv', header=0)

TCGAall = TCGAall[['case_id', 'submitter_id']]
TCGAstk = TCGAstk[['submitter_id', 'STK11']]

TCGAall = TCGAall.join(TCGAstk.set_index('submitter_id'), how='left', on='submitter_id')

TCGAall = TCGAall.fillna(0)
TCGAall = TCGAall.drop('case_id', axis=1)

TCGAall = TCGAall.rename(columns={'submitter_id': 'Slide_ID'})

TCGAall = TCGAall.join(TCGAim.set_index('Slide_ID'), how='inner', on='Slide_ID')
TCGAall = TCGAall.drop_duplicates()
lll = []
for idx, row in TCGAall.iterrows():
   lll.append(row['Slide_ID']+'-'+row['FileName'].split('-')[-2])
TCGAall['Slide_ID'] = lll

TCGAall.to_csv('TCGA_Joint.csv', index=False, header=True)

LUADlabel = pd.concat([Labelfile, TCGAall])
LUADlabel.to_csv('label.csv', index=False, header=True)

