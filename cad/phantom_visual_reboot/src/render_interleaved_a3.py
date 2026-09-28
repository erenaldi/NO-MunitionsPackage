"""Flush-panel/recess review, including the actual cut body and deployed exits."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
views = [
    ('Stowed','stowed_iso',[1,-1,.7],[0,0,0],1000,[0,0,1]),
    ('Stowed','stowed_opposed',[-1,1,.7],[0,0,0],1000,[0,0,1]),
    ('Stowed','stowed_top',[0,0,1],[0,0,0],1500,[1,0,0]),
    ('Stowed','stowed_side',[0,-1,0],[0,0,0],1200,[0,0,1]),
    ('Stowed','stowed_end',[-1,0,0],[0,0,0],140,[0,0,1]),
    ('Body_Pocket','pocket_iso',[1,-1,1],[0,0,0],1000,[0,0,1]),
    ('Midfold','mid_iso',[1,-1,.9],[0,0,0],1100,[0,0,1]),
    ('Deployed','deployed_iso',[1,-1,.9],[0,0,0],1100,[0,0,1]),
    ('Deployed','deployed_opposed',[-1,1,.7],[0,0,0],1100,[0,0,1]),
]
job = [{'input':f'STEP/O_Interleaved_A3_{state}.step','mode':'view','output':{'tightFrame':False},
        'outputs':[{'path':f'reviews/O_A3_{name}.png','camera':{'direction':direction,'up':up,
                    'target':target,'orthographicHalfHeight':height,'projection':'orthographic'}}]}
       for state,name,direction,target,height,up in views]
(ROOT/'review_interleaved_a3.json').write_text(json.dumps(job,indent=2)+'\n',encoding='utf-8')
(ROOT/'review_interleaved_a3_side.json').write_text(json.dumps([job[3]],indent=2)+'\n',encoding='utf-8')
