"""Serialized shape checks for the underside-only visual revision."""
from pathlib import Path
import build123d as bd

root = Path(__file__).resolve().parents[1]
old = bd.import_step(root / 'STEP/E_Transition_Nose_R2.step')
new = bd.import_step(root / 'STEP/F_Transition_Nose_R3.step')
close = bd.import_step(root / 'STEP/F_Transition_Nose_R3_Close.step')
for shape, length in [(new, 2800), (close, 850)]:
    assert shape.is_valid and len(shape.solids()) == 1
    assert abs(shape.bounding_box().size.X - length) < .001
    assert abs(shape.bounding_box().size.Y - 172) < .001
    assert abs(shape.bounding_box().size.Z - 172) < .001
    tip = max(shape.vertices(), key=lambda v: v.X)
    assert abs(tip.X-1400) < .001 and abs(tip.Z-40) < .001
for region in [bd.Box(2160, 400, 400).translate((-320, 0, 0))]:
    a, b = old & region, new & region
    assert (a-b).volume + (b-a).volume < .01
# Raising the side corners also changes the connected sloping side faces
# above Z=0. Entire-upper-half identity is therefore not an invariant.
# Check the retained roof datums directly on each exported section instead.
for x in [800, 900, 1010, 1100, 1300]:
    old_box = bd.section(old, section_by=bd.Plane.YZ.offset(x)).bounding_box()
    new_box = bd.section(new, section_by=bd.Plane.YZ.offset(x)).bounding_box()
    assert abs(old_box.max.Z-new_box.max.Z) < .001
    a, b = old_box.min.Z, new_box.min.Z
    assert b > a
    print(f'X={x}: underside Z {a:.3f} -> {b:.3f} mm')
print('PASS: both valid single solids; length, body, roof heights and apex preserved; underside raised. Connected side faces change.')
