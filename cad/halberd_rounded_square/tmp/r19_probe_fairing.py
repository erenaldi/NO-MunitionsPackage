"""Exploratory: booster fin-fairing clock span at the planned stage-ring stations."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[0] / "shared"))

from cadgen import build123d as bd  # noqa: E402
from surface_detail import _ray_hits, clock_frame  # noqa: E402
from halberd_r18_access_shapes import load_saved_parts  # noqa: E402

_, saved = load_saved_parts(ROOT / "STEP" / "halberd_r18_access.step")
fairing = saved["booster_fin_fairing_1"]
b = fairing.bounding_box()
for x in (-1124.0, -1130.33, -1148.5, -1200.0, -1300.0, -1400.0, -1470.0):
    hit_clocks = []
    for i in range(0, 181):
        clock = i * 0.5
        radial, _ = clock_frame(clock)
        if _ray_hits(fairing, bd.Vector(x, 0, 0) + radial * 260.0, -radial):
            hit_clocks.append(clock)
    span = (min(hit_clocks), max(hit_clocks)) if hit_clocks else None
    print(f"fairing_1 X={x}: clock span {span}")
for i in range(1, 5):
    c = saved[f"booster_fin_fairing_{i}"].center()
    print(i, "clock", math.degrees(math.atan2(c.Y, c.Z)) % 360)
    c = saved[f"main_fin_{i}"].center()
    print(i, "main fin clock", math.degrees(math.atan2(c.Y, c.Z)) % 360)
