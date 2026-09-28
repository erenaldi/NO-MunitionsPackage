"""Check exported R4 and exact preservation of the approved R3 regions."""
import json
from pathlib import Path
import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
old = bd.import_step(ROOT / 'STEP/F_Transition_Nose_R3.step')
new = bd.import_step(ROOT / 'STEP/G_Transition_Nose_R4.step')
close = bd.import_step(ROOT / 'STEP/G_Transition_Nose_R4_Close.step')
report = {}


def difference(a, b):
    return (a-b).volume + (b-a).volume


for name, shape, length in [('body', new, 2800), ('close', close, 850)]:
    assert shape.is_valid and len(shape.solids()) == 1 and shape.volume > 0
    box = shape.bounding_box()
    assert abs(box.size.X-length) < .001
    assert abs(box.size.Y-172) < .001 and abs(box.size.Z-172) < .001
    report[name] = dict(valid=True, solids=1, length_mm=box.size.X)

regions = {
    'square_barrel': bd.Box(2160, 400, 400).translate((-320, 0, 0)),
    'entire_pointed_nose': bd.Box(390, 400, 400).translate((1205, 0, 0)),
    'lower_shoulder_and_underside': bd.Box(3000, 400, 250).translate((0, 0, -75)),
}
for name, region in regions.items():
    delta = difference(old & region, new & region)
    assert delta < .01, (name, delta)
    report[name + '_difference_mm3'] = delta
crop = bd.Box(850, 400, 400).translate((975, 0, 0))
assert difference(new & crop, close) < .01
# The five replacement patches must remain symmetrical across the centerline.
upper = new & bd.Box(250, 400, 150).translate((885, 0, 125))
symmetry = difference(upper, upper.mirror(bd.Plane.XZ))
assert symmetry < .01, symmetry
report['upper_shoulder_mirror_difference_mm3'] = symmetry
roof_faces = [f for f in new.faces() if f.geom_type == bd.GeomType.PLANE
              and f.bounding_box().min.X > 759.99
              and f.bounding_box().max.X < 1010.01
              and min(v.Z for v in f.vertices()) > 73.99]
assert len(roof_faces) == 1 and len(roof_faces[0].vertices()) == 4
assert abs(roof_faces[0].area - 151*(250**2+12**2)**.5) < .01
report['roof_single_full_width_quadrilateral'] = True
report['roof_area_mm2'] = roof_faces[0].area
print(json.dumps(report, indent=2))
(ROOT / 'reviews/transition_r4_checks.json').write_text(
    json.dumps(report, indent=2)+'\n', encoding='utf-8')
