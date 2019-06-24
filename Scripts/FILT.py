"""
Filter out pos tiles with score less than 0.8

Created on 06/17/2019

@author: RH
"""

import pandas as pd
import os
import sys

dirr = sys.argv[1]  # name of output directory
File = pd.read_csv('../Results/I3_App/Positive/{}/out/finaldict.csv'.format(dirr), header=0)

pics = []

for index, row in File.iterrows():
    if row['POS_score'] > 0.99:
        pics.append(str(row['Num']))

f = []
for (dirpath, dirnames, filenames) in os.walk('../Results/I3_App/Positive/{}/out/Test_img'.format(dirr)):
    f.extend(filenames)
    break

bad = []
for i in f:
    if i.split('_')[0] not in pics:
        os.remove('../Results/I3_App/Positive/{}/out/Test_img/{}'.format(dirr, i))

