"""Dump label/bbox tree of the master Halberd detailed STEP (read-only)."""
from pathlib import Path

from cadgen import read_step

SOURCE = Path("AAM-44_Halberd_Detailed.step")
model = read_step(SOURCE)
print("label:", model.label)
print("n children:", len(model.children))


def walk(shape, depth=0):
    pad = "  " * depth
    bb = shape.bounding_box()
    print(f"{pad}{shape.label!r} vol={shape.volume/1e9:.6f} m^3 "
          f"x[{bb.min.X:8.1f},{bb.max.X:8.1f}] "
          f"y[{bb.min.Y:7.1f},{bb.max.Y:7.1f}] "
          f"z[{bb.min.Z:7.1f},{bb.max.Z:7.1f}]")
    for child in getattr(shape, "children", []):
        walk(child, depth + 1)


for part in model.children:
    walk(part)
