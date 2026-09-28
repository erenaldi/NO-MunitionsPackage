"""Four-tail review with saved-geometry aft-section diagnostic crops."""
import json
from cadgen import build123d as bd, read_step, srgb, step
from tail_fin_r1 import ROOT
from tail_fin_r3 import BODY_LABEL


def tail_focus(state):
    original = read_step(ROOT/f'STEP/Q_Tail_R4_Four_{state}.step')
    parts = {}
    def visit(p):
        if p.children:
            for child in p.children:
                visit(child)
        else:
            parts[p.label] = p
    visit(original)
    mask = bd.Box(380,1000,1000).translate((-1210,0,0))
    cropped = (parts[BODY_LABEL] & mask).clean()
    cropped.label = 'body_cropped_Xminus1400_to_minus1020_REVIEW_ONLY'
    cropped.color = srgb('#A7B4BC')
    tails = [p for label,p in parts.items() if label.startswith('tail_r4_')]
    assert len(tails) == 16 and cropped.is_valid and len(cropped.solids()) == 1
    return bd.Compound(children=[cropped,*tails],label='R4_AFT_CROP_REVIEW_ONLY_'+state)


@step(out='../STEP/Q_Tail_R4_Focus_Stowed.step')
def focus_stowed():
    return tail_focus('Stowed')


@step(out='../STEP/Q_Tail_R4_Focus_Deployed.step')
def focus_deployed():
    return tail_focus('Deployed')


def write_job():
    views = [
        ('Four_Stowed','stowed_iso',[1,-1,.7],[0,0,0],1000),
        ('Four_Stowed','stowed_opposed',[-1,1,.7],[0,0,0],1000),
        ('Four_Deployed','deployed_iso',[1,-1,.9],[0,0,0],1100),
        ('Four_Deployed','deployed_opposed',[-1,1,.7],[0,0,0],1100),
        ('Four_Midfold','midfold_iso',[1,-1,.9],[0,0,0],1100),
        ('Focus_Stowed','tail_stowed',[-1,1,1],[-1210,0,0],240),
        ('Focus_Deployed','tail_deployed',[-1,1,1],[-1210,0,0],260),
        ('Focus_Deployed','tail_opposed',[1,-1,-1],[-1210,0,0],260),
        ('Focus_Deployed','tail_end',[-1,0,0],[-1210,0,0],240),
    ]
    jobs = [{'input':f'STEP/Q_Tail_R4_{state}.step','mode':'view','output':{'tightFrame':False},
             'outputs':[{'path':f'reviews/Q_Tail_R4_{name}.png','camera':{
                 'direction':direction,'up':[0,0,1],'target':target,
                 'orthographicHalfHeight':height,'projection':'orthographic'}}]}
            for state,name,direction,target,height in views]
    (ROOT/'review_tail_fin_r4.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    focus_stowed()
    focus_deployed()
    write_job()
