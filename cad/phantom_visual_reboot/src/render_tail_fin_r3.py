"""Recessed clipped-fin review: flush stow, exposed pocket and folding poses."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
jobs = []
for state in ('Stowed','Midfold','Deployed','Body_Pocket'):
    jobs.append({'input':f'STEP/Q_Tail_R3_Recessed_{state}.step','mode':'view',
                 'output':{'tightFrame':False},'outputs':[{
                     'path':f'reviews/Q_Tail_R3_{state}_close.png','camera':{
                         'direction':[-1,1,2.5],'up':[0,0,1],'target':[-1125,0,60],
                         'orthographicHalfHeight':220,'projection':'orthographic'}}]})
jobs.append({'input':'STEP/Q_Tail_R3_Recessed_Stowed.step','mode':'view',
             'output':{'tightFrame':False},'outputs':[{
                 'path':'reviews/Q_Tail_R3_flush_side.png','camera':{
                     'direction':[0,1,0],'up':[0,0,1],'target':[-1205,0,60],
                     'orthographicHalfHeight':140,'projection':'orthographic'}}]})
jobs.append({'input':'STEP/Q_Tail_R3_Recessed_Deployed.step','mode':'view',
             'output':{'tightFrame':False},'outputs':[{
                 'path':'reviews/Q_Tail_R3_context.png','camera':{
                     'direction':[1,-1,.9],'up':[0,0,1],'target':[0,0,0],
                     'orthographicHalfHeight':1100,'projection':'orthographic'}}]})
(ROOT/'review_tail_fin_r3.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8')
