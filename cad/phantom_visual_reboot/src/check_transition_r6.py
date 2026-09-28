"""R6 exported geometry checks, including unchanged shared-factory defaults."""
import json
from pathlib import Path
import build123d as bd
from OCP.BRepAdaptor import BRepAdaptor_Surface
from transition_nose_r5 import body as r5_body

ROOT = Path(__file__).resolve().parents[1]
old = bd.import_step(ROOT/'STEP/H_Transition_Nose_R5.step')
new = bd.import_step(ROOT/'STEP/I_Transition_Nose_R6.step')


def difference(a,b):
    return (a-b).volume+(b-a).volume


report = {}
assert difference(old,r5_body())<.01
report['r5_factory_defaults_preserved'] = True
for suffix,length in [('',2800),('_Close',850),('_Tip',40)]:
    shape = bd.import_step(ROOT/('STEP/I_Transition_Nose_R6'+suffix+'.step'))
    assert shape.is_valid and len(shape.solids())==1 and shape.volume>0
    box = shape.bounding_box()
    assert abs(box.size.X-length)<.001 and abs(box.max.X-1400)<.001
    if suffix:
        crop = bd.Box(length,400,400).translate((1400-length/2,0,0))
        assert difference(new & crop,shape)<.01
    report[suffix or 'body'] = dict(valid=True,length_mm=box.size.X)
region = bd.Box(2410,400,400).translate((-195,0,0))
delta = difference(new & region,old & region)
assert delta<.01
report['body_and_shoulder_difference_mm3'] = delta
section = bd.section(new,section_by=bd.Plane.XY.offset(40))
leading = [e for e in section.edges() if e.bounding_box().min.X>1399.999]
assert len(leading)==1 and leading[0].geom_type==bd.GeomType.LINE
assert abs(leading[0].length-20)<.001
endpoints = sorted((v.X,v.Y,v.Z) for v in leading[0].vertices())
assert len(endpoints)==2
for actual,target in zip(endpoints,[(1400,-10,40),(1400,10,40)]):
    assert all(abs(a-b)<.001 for a,b in zip(actual,target))
report['finished_width_mm'] = leading[0].length
report['endpoints_mm'] = endpoints
faces = [f for f in new.faces() if f.geom_type==bd.GeomType.CYLINDER
         and f.bounding_box().min.X>1390]
assert len(faces)==1
cyl = BRepAdaptor_Surface(faces[0].wrapped).Cylinder()
assert abs(cyl.Radius()-4)<.000001
assert abs(cyl.Location().X()-1396)<.001 and abs(cyl.Location().Z()-40)<.001
assert abs(abs(cyl.Axis().Direction().Y())-1)<.000001
report['radius_mm'] = cyl.Radius()
nose = new & bd.Box(390,400,400).translate((1205,0,0))
assert difference(nose,nose.mirror(bd.Plane.XZ))<.01
report['symmetric_nose'] = True
print(json.dumps(report,indent=2))
(ROOT/'reviews/transition_r6_checks.json').write_text(
    json.dumps(report,indent=2)+'\n',encoding='utf-8')
