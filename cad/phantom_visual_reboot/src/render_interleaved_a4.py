"""Review both sides of A4's side-specific wing exit channels."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
views = [
    ('Stowed','stowed_iso',[1,-1,.7],[0,0,0],1000),
    ('Stowed','stowed_opposed',[-1,1,.7],[0,0,0],1000),
    ('Deployed','deployed_iso',[1,-1,.9],[0,0,0],1100),
    ('Deployed','deployed_opposed',[-1,1,.7],[0,0,0],1100),
    ('Deployed','port_channel_detail',[0,-1,.12],[50,0,70],430),
    ('Deployed','starboard_channel_detail',[0,1,.12],[50,0,70],430),
    ('Body_Pocket','pocket_port',[1,-1,1],[0,0,0],1000),
    ('Body_Pocket','pocket_starboard',[-1,1,1],[0,0,0],1000),
]
jobs = [{'input':f'STEP/O_Interleaved_A4_{state}.step','mode':'view','output':{'tightFrame':False},
         'outputs':[{'path':f'reviews/O_A4_{name}.png','camera':{
             'direction':direction,'up':[0,0,1],'target':target,
             'orthographicHalfHeight':height,'projection':'orthographic'}}]}
        for state,name,direction,target,height in views]
(ROOT/'review_interleaved_a4.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8')
