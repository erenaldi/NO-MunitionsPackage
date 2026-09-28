"""Serialized R7 symmetry and one-panel rigid folding/clearance checks."""
import json
import math
from pathlib import Path
import build123d as bd

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return bd.import_step(ROOT/'STEP'/name)


def difference(a,b):
    return (a-b).volume+(b-a).volume


body = load('J_Symmetric_Body_R7.step')
prior = load('I_Transition_Nose_R6.step')
close = load('J_Symmetric_Body_R7_Close.step')
for part in (body,close):
    assert part.is_valid and len(part.solids())==1 and part.volume>0
mirror_delta = difference(body,body.mirror(bd.Plane.XZ))
assert mirror_delta<.01
for region in [bd.Box(390,400,400).translate((1205,0,0)),
               bd.Box(2160,400,400).translate((-320,0,0)),
               bd.Box(250,400,150).translate((885,0,125))]:
    assert difference(body & region,prior & region)<.01
assert difference(body & bd.Box(850,400,400).translate((975,0,0)),close)<.01
lower_faces = [f for f in body.faces() if f.bounding_box().min.X>759.99
               and f.bounding_box().max.X<1010.01
               and min(v.Z for v in f.vertices())<-70]
left = sorted(f.area for f in lower_faces if f.center().Y<0)
right = sorted(f.area for f in lower_faces if f.center().Y>0)
assert len(left)==len(right)==3
assert all(abs(a-b)<.001 for a,b in zip(left,right))
report = dict(body_mirror_difference_mm3=mirror_delta,
              lower_shoulder_left_face_areas_mm2=left,
              lower_shoulder_right_face_areas_mm2=right)

axis = bd.Axis((-160,0,0),(0,0,1))
poses = {}
for state,angle in [('Deployed',0),('Midfold',-45),('Stowed',-90)]:
    assembly = load('K_Wing_Prototype_R1_'+state+'.step')
    parts = {c.label:c for c in assembly.children}
    assert len(parts)==4
    assert all(p.is_valid and len(p.solids())==1 and p.volume>0 for p in parts.values())
    assert abs(assembly.bounding_box().size.X-2800)<.001
    pbody = parts['RDM9_R7_symmetric_body_20mm_wedge_R4']
    assert difference(body,pbody)<.01
    poses[state] = parts
    if state=='Stowed':
        radial_bounds = {}
        for label,part in parts.items():
            box=part.bounding_box()
            bound=math.hypot(max(abs(box.min.Y),abs(box.max.Y)),
                             max(abs(box.min.Z),abs(box.max.Z)))
            assert bound<125, (label,bound)
            radial_bounds[label]=bound
        report['stowed_conservative_radial_bounds_mm']=radial_bounds
    if state!='Deployed':
        for label,part in parts.items():
            base=poses['Deployed'][label]
            restored=part.rotate(axis,-angle) if label=='prototype_starboard_wing' else part
            assert difference(base,restored)<.01, label

deployed=poses['Deployed']
wing=deployed['prototype_starboard_wing']
saddle=deployed['prototype_hinge_saddle']
pin=deployed['prototype_hinge_pin_and_cap']
assert (saddle & body).volume>1 and (saddle & pin).volume>.1
assert abs(wing.bounding_box().max.Y-650)<.001
assert abs(wing.bounding_box().size.Z-4)<.001
clearances=[]
for angle in range(-90,1,5):
    panel=wing.rotate(axis,angle)
    for fixed in [body,saddle,pin]:
        overlap=panel & fixed
        assert overlap is None or overlap.volume<.001
    clearances.append(dict(angle_deg=angle,body_mm=panel.distance_to(body),
                           saddle_mm=panel.distance_to(saddle),pin_mm=panel.distance_to(pin)))
    assert clearances[-1]['body_mm']>3.49
    assert clearances[-1]['saddle_mm']>.49
    assert clearances[-1]['pin_mm']>.099
report['sampled_fold_clearances']=clearances
report['panel_identity_all_poses']=True
report['wing_thickness_mm']=4
report['hinge_to_tip_span_mm']=650
print(json.dumps(report,indent=2))
(ROOT/'reviews/body_wing_r1_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
