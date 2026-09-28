"""A2 matched views and explicitly exploded saved-housing support diagnostic."""
import json
from pathlib import Path
from cadgen import step, read_step, build123d as bd
from interleaved_wing_a import box, tag

ROOT = Path(__file__).resolve().parents[1]


@step(out='../STEP/O_Interleaved_A2_Support_Exploded.step')
def support_exploded():
    saved = read_step(ROOT/'STEP/O_Interleaved_A2_Stowed.step')
    housing = next(p for p in saved.children if p.label == 'supported_housing')
    base = tag(housing & box(-500,600,-100,100,85,88), 'base_actual_position', '#697B84')
    supports = tag(housing & box(-500,600,-100,100,88,93), 'supports_actual_position', '#BA9048')
    deck = tag((housing & box(-500,600,-100,100,93,100)).translate((0,-100,50)),
               'shelf_shift_Yminus100_Zplus50_FOR_REVIEW_ONLY', '#9EABB4')
    return bd.Compound(children=[base,supports,deck], label='A2_EXPLODED_SUPPORT_REVIEW_NOT_ASSEMBLY')


def jobs():
    items = []
    def add(state,name,direction,target,hh,up=(0,0,1)):
        items.append({'input':f'STEP/O_Interleaved_A2_{state}.step','mode':'view',
                      'output':{'tightFrame':False},
                      'outputs':[{'path':f'reviews/O_A2_{name}.png','camera':{
                          'direction':direction,'up':up,'target':target,'orthographicHalfHeight':hh,'projection':'orthographic'}}]})
    add('Module_Stowed','module_end',[-1,0,0],[0,0,97],65)
    add('Module_Stowed','module_iso',[1,-1,.5],[50,0,96],340)
    add('Deployed','deployed_iso',[1,-1,.9],[0,0,0],1100)
    add('Deployed','deployed_opposed',[-1,1,.7],[0,0,1],1100)
    add('Support_Exploded','support_exploded',[1,1,1.5],[50,-30,110],370)
    add('Support_Exploded','support_end',[-1,0,0],[0,-50,110],160)
    (ROOT/'review_interleaved_a2.json').write_text(json.dumps(items,indent=2)+'\n',encoding='utf-8')
    (ROOT/'review_interleaved_a2_support.json').write_text(json.dumps(items[-2:],indent=2)+'\n',encoding='utf-8')
    (ROOT/'review_interleaved_a2_end.json').write_text(json.dumps(items[-1:],indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    support_exploded()
    jobs()
