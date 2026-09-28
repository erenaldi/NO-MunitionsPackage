"""Reduced-travel intake review using the original R1 camera scale."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
views = [
    ('deployed_belly',[1,-1,-.8],[0,0,0],1100),
    ('deployed_side',[0,1,0],[-620,0,-85],320),
    ('mouth',[1,0,-.3],[-300,0,-111],110),
]
jobs = [{'input':'STEP/R_RampIntake_R2_Deployed.step','mode':'view','output':{'tightFrame':False},
         'outputs':[{'path':f'reviews/R_Intake_R2_{name}.png','camera':{
             'direction':direction,'up':[0,0,1],'target':target,
             'orthographicHalfHeight':height,'projection':'orthographic'}}]}
        for name,direction,target,height in views]
(ROOT/'review_ramp_intake_r2.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8')
