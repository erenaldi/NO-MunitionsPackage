"""Sketch-led ventral ramp review: side silhouette, closed belly and open mouth."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
views = [
    ('Stowed','stowed_belly',[1,-1,-.8],[0,0,0],1000),
    ('Deployed','deployed_belly',[1,-1,-.8],[0,0,0],1100),
    ('Deployed','deployed_opposed',[-1,1,-.8],[0,0,0],1100),
    ('Stowed','stowed_side',[0,1,0],[-620,0,-85],320),
    ('Deployed','deployed_side',[0,1,0],[-620,0,-85],320),
    ('Deployed','mouth',[1,0,-.3],[-300,0,-111],110),
    ('Body_Cavity','body_cavity',[1,-1,-.8],[0,0,0],1000),
    ('Module_Stowed','module_stowed',[1,-1,.8],[-620,0,-70],230),
    ('Module_Deployed','module_deployed',[1,-1,.8],[-620,0,-90],230),
]
jobs = [{'input':f'STEP/R_RampIntake_R1_{state}.step','mode':'view','output':{'tightFrame':False},
         'outputs':[{'path':f'reviews/R_Intake_R1_{name}.png','camera':{
             'direction':direction,'up':[0,0,1],'target':target,
             'orthographicHalfHeight':height,'projection':'orthographic'}}]}
        for state,name,direction,target,height in views]
(ROOT/'review_ramp_intake_r1.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8')
