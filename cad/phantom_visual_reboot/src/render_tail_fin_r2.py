"""Aft-shifted clipped-fin views matched to the R1 comparison cameras."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
jobs = []
for state in ('Stowed','Midfold','Deployed'):
    jobs.append({'input':f'STEP/Q_Tail_R2_Clipped_{state}.step','mode':'view',
                 'output':{'tightFrame':False},'outputs':[{
                     'path':f'reviews/Q_Tail_R2_{state}_close.png','camera':{
                         'direction':[-1,1,2.5],'up':[0,0,1],'target':[-1125,0,60],
                         'orthographicHalfHeight':220,'projection':'orthographic'}}]})
jobs.append({'input':'STEP/Q_Tail_R2_Clipped_Deployed.step','mode':'view',
             'output':{'tightFrame':False},'outputs':[{
                 'path':'reviews/Q_Tail_R2_context.png','camera':{
                     'direction':[1,-1,.9],'up':[0,0,1],'target':[0,0,0],
                     'orthographicHalfHeight':1100,'projection':'orthographic'}}]})
(ROOT/'review_tail_fin_r2.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8')
