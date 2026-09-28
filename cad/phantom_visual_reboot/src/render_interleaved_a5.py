"""A5 covered assembly and calculated pin-exit review cameras."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
views = [
    ('Stowed','stowed_iso',[1,-1,.7],[0,0,0],1000),
    ('Stowed','stowed_opposed',[-1,1,.7],[0,0,0],1000),
    ('Midfold','mid_iso',[1,-1,.9],[0,0,0],1100),
    ('Deployed','deployed_iso',[1,-1,.9],[0,0,0],1100),
    ('Deployed','deployed_opposed',[-1,1,.7],[0,0,0],1100),
    ('Body_Pocket','pocket_iso',[1,-1,1],[0,0,0],1000),
    ('Body_Pocket','port_pin_exit',[-1,-2,.8],[-399,-80,70],35),
    ('Body_Pocket','starboard_pin_exit',[-1,2,.8],[-399,80,65],35),
]
jobs = [{'input':f'STEP/O_Interleaved_A5_{state}.step','mode':'view','output':{'tightFrame':False},
         'outputs':[{'path':f'reviews/O_A5_{name}.png','camera':{
             'direction':direction,'up':[0,0,1],'target':target,
             'orthographicHalfHeight':height,'projection':'orthographic'}}]}
        for state,name,direction,target,height in views]
(ROOT/'review_interleaved_a5.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8')
