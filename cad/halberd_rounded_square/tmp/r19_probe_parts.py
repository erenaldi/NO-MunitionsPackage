"""Exploratory: list R18 access parts with bounds, then probe host skin radii."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[0] / "shared"))

from cadgen import build123d as bd  # noqa: E402
from surface_detail import skin_point  # noqa: E402
from halberd_r18_access_shapes import load_saved_parts  # noqa: E402

scene, saved = load_saved_parts(ROOT / "STEP" / "halberd_r18_access.step")
for label, part in saved.items():
    b = part.bounding_box()
    print(f"{label:40s} X[{b.min.X:9.2f},{b.max.X:9.2f}] Y[{b.min.Y:8.2f},{b.max.Y:8.2f}] "
          f"Z[{b.min.Z:8.2f},{b.max.Z:8.2f}] faces={len(part.faces())}")

for host_label, xs in (("main_body_intake_r12", (1080, 1000, 800, 690, 600, 400, 0, -400, -800, -1000, -1100)),
                       ("booster_body", (-1130, -1200, -1300, -1400, -1500, -1600, -1650, -1680))):
    host = saved[host_label]
    print("==", host_label)
    for x in xs:
        row = []
        for clock in range(0, 360, 15):
            try:
                r = skin_point(host, x, 0.0, clock)["measured_radius_mm"]
                row.append(f"{r:6.1f}")
            except Exception as exc:  # noqa: BLE001
                row.append("  miss")
        print(f"X={x:6d} " + " ".join(row))
