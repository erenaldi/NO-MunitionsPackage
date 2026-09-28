"""Probe the saved J/R7 body cross-section at the wing stations."""
import math
from pathlib import Path
import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
body = bd.import_step(ROOT / 'STEP/J_Symmetric_Body_R7.step')
print('body bbox:', body.bounding_box())
for x in (500.0, 200.0, -250.0, -400.0, 0.0):
    cut = body & bd.Box(2, 400, 400).translate((x, 0, 0))
    if cut is None or cut.volume == 0:
        print(f'X={x}: empty')
        continue
    bb = cut.bounding_box()
    print(f'X={x}: Y [{bb.min.Y:.2f}, {bb.max.Y:.2f}] Z [{bb.min.Z:.2f}, {bb.max.Z:.2f}]')
# body surface height at Y=0 and Y=30 (top of body at those Y)
for y in (0.0, 30.0, -30.0, 60.0):
    cut = body & bd.Box(400, 2, 400).translate((300, y, 0))
    if cut is None or cut.volume == 0:
        print(f'Y={y}: empty')
        continue
    bb = cut.bounding_box()
    print(f'Y={y}: X [{bb.min.X:.2f}, {bb.max.X:.2f}] Z [{bb.min.Z:.2f}, {bb.max.Z:.2f}]')