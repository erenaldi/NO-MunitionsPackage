"""Measure the finished rounded wedge on serialized STEP, not construction stock."""
import json
from pathlib import Path
import build123d as bd
from OCP.BRepAdaptor import BRepAdaptor_Surface

ROOT = Path(__file__).resolve().parents[1]
old = bd.import_step(ROOT / 'STEP/G_Transition_Nose_R4.step')
new = bd.import_step(ROOT / 'STEP/H_Transition_Nose_R5.step')
report = {}


def difference(a,b):
    return (a-b).volume+(b-a).volume


for suffix, length in [('',2800),('_Close',850),('_Tip',40)]:
    part = bd.import_step(ROOT / ('STEP/H_Transition_Nose_R5'+suffix+'.step'))
    assert part.is_valid and len(part.solids()) == 1 and part.volume > 0
    box = part.bounding_box()
    assert abs(box.size.X-length)<.001 and abs(box.max.X-1400)<.001
    report[suffix or 'body'] = dict(valid=True, solids=1, length_mm=box.size.X)
    if suffix:
        crop = bd.Box(length,400,400).translate((1400-length/2,0,0))
        assert difference(new & crop, part)<.01

retained = bd.Box(2410,400,400).translate((-195,0,0))
delta = difference(old & retained, new & retained)
assert delta<.01
report['body_and_cleaned_shoulder_difference_mm3'] = delta
section = bd.section(new, section_by=bd.Plane.XY.offset(40))
leading = [e for e in section.edges() if e.bounding_box().min.X>1399.999]
assert len(leading)==1
edge = leading[0]
assert edge.geom_type==bd.GeomType.LINE and abs(edge.length-10)<.001
ends = sorted((v.X,v.Y,v.Z) for v in edge.vertices())
assert len(ends)==2
for actual, target in zip(ends, [(1400,-5,40),(1400,5,40)]):
    assert all(abs(a-b)<.001 for a,b in zip(actual,target))
report['finished_leading_edge_width_mm'] = edge.length
report['finished_leading_edge_endpoints_mm'] = ends
curved = [f for f in new.faces() if f.geom_type==bd.GeomType.CYLINDER
          and f.bounding_box().min.X>1390]
assert len(curved)==1
cylinder = BRepAdaptor_Surface(curved[0].wrapped).Cylinder()
assert abs(cylinder.Radius()-1)<.000001
assert abs(cylinder.Location().X()-1399)<.001
assert abs(cylinder.Location().Z()-40)<.001
assert abs(abs(cylinder.Axis().Direction().Y())-1)<.000001
report['leading_edge_radius_mm'] = cylinder.Radius()
nose = new & bd.Box(390,400,400).translate((1205,0,0))
assert difference(nose,nose.mirror(bd.Plane.XZ))<.01
report['nose_symmetry'] = True
print(json.dumps(report,indent=2))
(ROOT/'reviews/transition_r5_checks.json').write_text(
    json.dumps(report,indent=2)+'\n',encoding='utf-8')
