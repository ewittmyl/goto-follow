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

with open("processed_id.txt") as f:
    processed_event = [s.split('\n')[0] for s in f.readlines()]

for fid in fermi_id:
    if not fid in processed_event:
        if not os.path.isdir('./{}'.format(fid)):
            os.mkdir('./{}'.format(fid))
        os.chdir('./{}'.format(fid))
        gf.GenerateReports.TemplateComparing(fid, day=1, subtract=False, score=0.5, near_galaxy=True)
        os.system("rm -rf *.fz")
        os.chdir('../')
        with open("processed_id.txt", 'a+') as f:
            f.writelines('{}\n'.format(fid)) 

