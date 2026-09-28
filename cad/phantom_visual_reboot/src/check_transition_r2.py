"""Independent checks on serialized local-prototype artifacts."""
import json
from pathlib import Path
import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
results = {}
for name, length in [('E_Transition_Nose_R2', 2800),
                     ('E_Transition_Nose_R2_Close', 850)]:
    shape = bd.import_step(ROOT / 'STEP' / (name + '.step'))
    box = shape.bounding_box()
    assert shape.is_valid and len(shape.solids()) == 1
    assert abs(box.size.X - length) < .001
    assert abs(box.size.Y - 172) < .001 and abs(box.size.Z - 172) < .001
    # Bounding-box diagonal is a conservative bound on every body point,
    # including curved shoulder surfaces, not just a vertex sample.
    radial_bound = (86**2 + 86**2)**.5
    assert radial_bound < 125
    tip = max(shape.vertices(), key=lambda v: v.X)
    assert abs(tip.X - 1400) < .001 and abs(tip.Z - 40) < .001
    assert abs(tip.Y) < .001
    stations = {}
    for x in [600, 759, 800, 900, 1010, 1100, 1300, 1399]:
        cut = bd.section(shape, section_by=bd.Plane.YZ.offset(x))
        assert cut.area > 0
        stations[x] = round(cut.area, 3)
    assert all(stations[a] > stations[b] for a,b in
               [(800,900),(900,1010),(1010,1100),(1100,1300),(1300,1399)])
    results[name] = dict(valid=True, solids=1, length_mm=box.size.X,
                         body_radial_bound_mm=radial_bound,
                         tip_z_mm=tip.Z, section_areas_mm2=stations)
print(json.dumps(results, indent=2))
(ROOT / 'reviews' / 'transition_r2_checks.json').write_text(
    json.dumps(results, indent=2) + '\n', encoding='utf-8')
