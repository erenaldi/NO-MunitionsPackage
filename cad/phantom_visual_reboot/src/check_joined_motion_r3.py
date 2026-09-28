"""Move serialized parts: 21 simultaneous deployment samples, no regenerated panels."""
import json
import itertools
from pathlib import Path
import build123d as bd
from check_joined_wing_r3 import canonical, difference, volume
from joined_wing_r3 import pose, place_panel

ROOT=Path(__file__).resolve().parents[1]
base={p.label:p for p in bd.import_step(ROOT/'STEP/N_JoinedWing_R3_Stowed.step').children}
panels={side+'_'+kind:canonical(base[side+'_'+kind],side,kind)
        for side in ('port','starboard') for kind in ('front','rear')}


def moved(f):
    result=dict(base)
    for side in ('port','starboard'):
        for kind in ('front','rear'):
            label=side+'_'+kind
            result[label]=place_panel(panels[label],side,kind,f)
        start,end=pose(0,side),pose(f,side)
        for kind,key in [('carriage','rear'),('join','joint')]:
            dx=end[key][0]-start[key][0]
            dy=end[key][1]-start[key][1]
            result[side+'_'+kind]=base[side+'_'+kind].translate((dx,dy,0))
    return result


report={'scope':'21 simultaneous samples; continuous sweep, strength, actuation, locks and rack unverified',
        'samples':[],'saved_pose_identity':{},'failures':[]}
for state,f in [('Midfold',.5),('Deployed',1)]:
    saved={p.label:p for p in bd.import_step(ROOT/('STEP/N_JoinedWing_R3_'+state+'.step')).children}
    expected=moved(f)
    assert set(saved)==set(expected)
    assert all(p.is_valid and len(p.solids())==1 and p.volume>0 for p in saved.values())
    deltas={label:difference(saved[label],p) for label,p in expected.items()}
    assert max(deltas.values())<.01,deltas
    report['saved_pose_identity'][state]=deltas

for i in range(21):
    print('Motion sample',i,'/20',flush=True)
    parts=moved(i/20)
    minimum=1e9
    for a,b in itertools.combinations(parts,2):
        is_panel=a in panels or b in panels
        gap=parts[a].distance_to(parts[b])
        if is_panel:
            minimum=min(minimum,gap)
            if gap<=.2:
                report['failures'].append([i/20,a,b,'panel clearance',gap])
        # Fixed roots intentionally overlap base/body; base seated on body.
        support_pair=(a=='supported_housing' and (b.endswith('fixed_root') or b.startswith('RDM9_'))) or (b=='supported_housing' and (a.endswith('fixed_root') or a.startswith('RDM9_')))
        support_pair=support_pair or (a.startswith('RDM9_') and b.endswith('fixed_root')) or (b.startswith('RDM9_') and a.endswith('fixed_root'))
        if gap<.001 and not support_pair:
            overlap=volume(parts[a]&parts[b])
            if overlap>=.001:
                report['failures'].append([i/20,a,b,'overlap',overlap])
    for side in ('port','starboard'):
        gap=parts[side+'_carriage'].distance_to(parts['supported_housing'])
        if gap>.001:
            report['failures'].append([i/20,side,'carriage support',gap])
    report['samples'].append({'fraction':i/20,'minimum_panel_clearance_mm':minimum})
report['passed']=not report['failures']
(ROOT/'reviews/joined_wing_r3_motion_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
if not report['passed']:
    raise SystemExit(1)
