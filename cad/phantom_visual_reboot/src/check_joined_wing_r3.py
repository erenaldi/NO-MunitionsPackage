"""Saved stowed candidate evidence; retain all diagnostics on failure."""
import json
import math
from pathlib import Path
import build123d as bd
from joined_wing_r3 import LAYERS
from joined_wing_r1 import pose

ROOT=Path(__file__).resolve().parents[1]


def volume(s):
    return 0 if s is None else s.volume


def difference(a,b):
    return volume(a-b)+volume(b-a)


def canonical(part,side,kind):
    p=pose(0)
    if side=='port':
        part=part.mirror(bd.Plane.XZ)
    x,y=p[kind]
    z=LAYERS[side][0 if kind=='rear' else 1]
    return part.translate((-x,-y+5,-z)).rotate(bd.Axis.Z,-p[kind+'_angle'])


def main():
    full=bd.import_step(ROOT/'STEP/N_JoinedWing_R3_Stowed.step')
    parts={p.label:p for p in full.children}
    old={p.label:p for p in bd.import_step(ROOT/'STEP/M_JoinedWing_R2_Stowed.step').children}
    panels=[side+'_'+kind for side in LAYERS for kind in ('front','rear')]
    failures=[]
    report={'scope':'stowed only; deployment unverified','parts':{},'panel_pairs':[], 'identity_mm3':{},'support_contacts':[]}
    body_name='RDM9_R7_symmetric_body_20mm_wedge_R4'
    report['body_difference_mm3']=difference(parts[body_name],old[body_name])
    if report['body_difference_mm3']>.01:
        failures.append('body changed')
    for name,part in parts.items():
        b=part.bounding_box()
        radius=math.hypot(max(abs(b.min.Y),abs(b.max.Y)),max(abs(b.min.Z),abs(b.max.Z)))
        valid=part.is_valid and len(part.solids())==1 and part.volume>0
        report['parts'][name]={'valid_single_solid':valid,'radial_bound_mm':radius}
        if not valid or radius>=125:
            failures.append((name,'valid/envelope',valid,radius))
    for side in LAYERS:
        for kind,oldname,oldz in [('front','forward_lifting_panel',98),('rear','rear_lifting_panel',91)]:
            p=pose(0)
            x,y=p[kind]
            ref=old[oldname].translate((-x,-y,-oldz)).rotate(bd.Axis.Z,-p[kind+'_angle'])
            delta=difference(canonical(parts[side+'_'+kind],side,kind),ref)
            report['identity_mm3'][side+'_'+kind]=delta
            if delta>.01:
                failures.append((side,kind,'panel identity',delta))
    for name in panels:
        print('Checking',name,flush=True)
        for other,shape in parts.items():
            if other==name:
                continue
            gap=parts[name].distance_to(shape)
            overlap=volume(parts[name]&shape)
            report['panel_pairs'].append({'a':name,'b':other,'clearance_mm':gap,'overlap_mm3':overlap})
            if gap<=.2 or overlap>=.001:
                failures.append((name,other,'interference',gap,overlap))
    # Each fixed support and carriage is seated on the single connected housing.
    for name in [body_name,*[side+'_'+kind for side in LAYERS for kind in ('fixed_root','carriage')]]:
        gap=parts[name].distance_to(parts['supported_housing'])
        overlap=volume(parts[name]&parts['supported_housing'])
        report['support_contacts'].append({'part':name,'gap_mm':gap,'overlap_mm3':overlap})
        if gap>.001:
            failures.append((name,'unsupported',gap))
    report['failures']=failures
    report['passed']=not failures
    (ROOT/'reviews/joined_wing_r3_stowed_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':not failures,'failures':failures},indent=2))
    if failures:
        raise SystemExit(1)


if __name__=='__main__':
    main()
