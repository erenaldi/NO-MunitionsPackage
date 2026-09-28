"""Matched one-corner tail planform studies; no fourfold propagation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
jobs = []
for variant in ('Compact','Swept','Tall'):
    for state in ('Stowed','Midfold','Deployed'):
        jobs.append({'input':f'STEP/Q_Tail_R1_{variant}_{state}.step','mode':'view',
                     'output':{'tightFrame':False},'outputs':[{
                         'path':f'reviews/Q_Tail_R1_{variant}_{state}_close.png',
                         'camera':{'direction':[-1,1,2.5],'up':[0,0,1],'target':[-1125,0,60],
                                   'orthographicHalfHeight':220,'projection':'orthographic'}}]})
    jobs.append({'input':f'STEP/Q_Tail_R1_{variant}_Deployed.step','mode':'view',
                 'output':{'tightFrame':False},'outputs':[{
                     'path':f'reviews/Q_Tail_R1_{variant}_context.png',
                     'camera':{'direction':[1,-1,.9],'up':[0,0,1],'target':[0,0,0],
                               'orthographicHalfHeight':1100,'projection':'orthographic'}}]})
(ROOT/'review_tail_fin_r1.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8')
