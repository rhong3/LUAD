# CPTAC Images Join
import pandas as pd
import numpy as np

imglist = pd.read_csv('../CPTAC-LUAD-HEslide-filename-mapping_Jan2019.csv', header=0)

samplelist = pd.read_csv('../CPTAC_LUAD.csv', header=0)

imglist = imglist[['Slide_ID', 'FileName']]

samplelist = samplelist.join(imglist.set_index('Slide_ID'), how='inner', on='Slide_ID')

samplelist = samplelist.dropna(subset=['FileName'])

samplelist = samplelist.drop(['Pathology'], axis=1)

samplelist.to_csv('../CPTAC_Joint_Images.csv', index=False, header=True)
