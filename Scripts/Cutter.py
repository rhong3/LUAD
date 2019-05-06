"""
Tile svs/scn files

Created on 11/01/2018

@author: RH
"""

import time
import matplotlib
import os
import shutil
import pandas as pd
matplotlib.use('Agg')
import Slicer

def cut():
    ref = pd.read_csv('../label.csv', header=0)
    level = 0
    # cut tiles with coordinates in the name (exclude white)
    start_time = time.time()

    for index, row in ref.iterrows():
        if 'TCGA' in row['Slide_ID']:
            tff = 2
            fd = 'TCGA/'
        else:
            tff = 1
            fd = 'CPTAC/'
        try:
            os.mkdir("../tiles/{}".format(row['Slide_ID']))
        except FileExistsError:
            pass
        try:
            os.mkdir("../tiles/{}/level{}".format(row['Slide_ID'], str(level)))
            dup = False
        except FileExistsError:
            dup = True
            pass
        otdir = "../tiles/{}/level{}".format(row['Slide_ID'], str(level))
        try:
            os.mkdir(otdir)
        except FileExistsError:
            pass
        try:
            n_x, n_y, raw_img, resx, resy, ct = Slicer.tile(image_file=fd + row['FileName'], outdir=otdir,
                                                            level=level, dp=dup, ft=tff)
        except IndexError:
            pass
        if len(os.listdir(otdir)) < 2:
            shutil.rmtree(otdir, ignore_errors=True)

    print("--- %s seconds ---" % (time.time() - start_time))

    # # Time measure tool
    # start_time = time.time()
    # print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    if not os.path.isdir('../tiles'):
        os.mkdir('../tiles')
    cut()

