import gotocat as gc
import numpy as np
import pandas as pd
import gotofollow as gf
import os

# load gotocat database
g = gc.GOTOdb()

# get all fermi trigger id
cmd = """SELECT DISTINCT target FROM image WHERE target LIKE 'Fermi%' ORDER BY target DESC"""
fermi_df = g.query(cmd)
fermi_id = [s.split('_T')[0] for s in fermi_df['target'].values]
fermi_id = list(set(fermi_id))
fermi_id.sort(reverse=True)

for fid in fermi_id:
    if os.path.isdir('./{}'.format(fid)):
        os.mkdir('./{}'.format(fid))
    os.chdir('./{}'.format(fid))
    gf.
    os.chdir('../')

