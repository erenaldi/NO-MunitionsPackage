"""Exploratory: which native skin faces each planned R19 panel footprint crosses."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[0] / "shared"))

from surface_detail import skin_point  # noqa: E402
from halberd_r18_access_shapes import load_saved_parts  # noqa: E402
from halberd_r19_surface_build import PANELS  # noqa: E402

_, saved = load_saved_parts(ROOT / "STEP" / "halberd_r18_access.step")
for pid, host, clock, x, t0, shape, size, _screws in PANELS:
    length, width = (size[0], size[0]) if shape == "round" else size
    faces = []
    for i in range(9):
        for j in range(5):
            dx = -length / 2 + length * i / 8
            dt = -width / 2 + width * j / 4
            try:
                f = skin_point(saved[host], x + dx, t0 + dt, clock)["face"]
            except Exception as exc:  # noqa: BLE001
                print(pid, "probe failed", dx, dt, exc)
                continue
            if not any(f.is_same(e) for e in faces):
                faces.append(f)
    info = [(round(f.bounding_box().min.X, 1), round(f.bounding_box().max.X, 1), str(f.geom_type))
            for f in faces]
    flag = "  <-- multi-face" if len(faces) > 1 else ""
    print(pid, len(faces), info, flag)
