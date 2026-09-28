"""Bounded R3 packaging/motion review cameras."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
views=[('Stowed','end',[-1,0,0],[0,0,1],[0,0,0],140),
       ('Module_Stowed','module_iso',[1,-1,.5],[0,0,1],[50,0,96],340),
       ('Module_Stowed','module_end',[-1,0,0],[0,0,1],[0,0,97],65),
       ('Stowed','body_iso',[1,-1,.7],[0,0,1],[0,0,0],1000),
       ('Midfold','mid_top',[0,0,1],[1,0,0],[0,0,0],1500),
       ('Deployed','deployed_top',[0,0,1],[1,0,0],[0,0,0],1500),
       ('Deployed','deployed_iso',[1,-1,.9],[0,0,1],[0,0,0],1100),
       ('Deployed','deployed_opposed',[-1,1,.7],[0,0,1],[0,0,0],1100)]
job=[{'input':'STEP/N_JoinedWing_R3_'+state+'.step','mode':'view','output':{'tightFrame':False},
      'outputs':[{'path':'reviews/N3_'+name+'.png','camera':{'direction':direction,'up':up,'target':target,'orthographicHalfHeight':hh,'projection':'orthographic'}}]}
     for state,name,direction,up,target,hh in views]
(ROOT/'review_N.json').write_text(json.dumps(job,indent=2)+'\n',encoding='utf-8')
