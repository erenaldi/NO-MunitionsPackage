"""Verification of candidate straight lowerings against the actual donor pylon surface (READ-ONLY study; nothing is applied).

Same method as checks/check_agm1_reference_fit.py (pylon triangle faces vs candidate solids; report intersection AREA), run on the
saved B2H Stowed leaves that have material above Z=40, with the pylon raised by d mm (equivalent to lowering the candidate by d).
"""
import json, sys
from pathlib import Path
import numpy as np
import build123d as bd
from cadgen import read_scene

ROOT = Path(__file__).resolve().parents[1]
D_VALUES = [float(x) for x in sys.argv[1:]] or [8.1, 9.1, 9.574]
raw = json.loads((ROOT / "reference/agm1_mount/pylon_candidate_frame.json").read_text(encoding="utf-8"))
pts0 = np.array(raw["vertices_CAD_mm"], float)
tris = raw["triangles"]
scene = read_scene(str(ROOT / "STEP" / "S_EngineBay_B2H_Stowed_Full.step"))
parts = {str(o.label): o.shape() for o in scene.leaves()}
top = {n: p for n, p in parts.items() if p.bounding_box(optimal=False).max.Z > 40.0}
boxes = {n: p.bounding_box() for n, p in top.items()}
out = {"candidate": "STEP/S_EngineBay_B2H_Stowed_Full.step", "leaves_tested": sorted(top), "results": {}}
for d in D_VALUES:
    pts = pts0 + np.array([0.0, 0.0, d])
    hits = {}
    for idx in tris:
        tri = pts[idx]
        lo, hi = tri.min(axis=0), tri.max(axis=0)
        cand = [n for n, b in boxes.items() if all(lo[k] <= tuple(b.max)[k] and hi[k] >= tuple(b.min)[k] for k in range(3))]
        if not cand or np.linalg.norm(np.cross(tri[1] - tri[0], tri[2] - tri[0])) < 1e-9:
            continue
        face = bd.Face(bd.Wire.make_polygon([tuple(v) for v in tri], close=True))
        for n in cand:
            common = face & top[n]
            area = 0.0 if common is None else float(common.area)
            if area > 1e-6:
                e = hits.setdefault(n, {"triangle_count": 0, "intersection_area_mm2": 0.0})
                e["triangle_count"] += 1
                e["intersection_area_mm2"] += area
    lowest = float(pts[:, 2].min())
    out["results"][str(d)] = {"lowering_mm": d, "pylon_lowest_z_after_mm": lowest,
                              "bbox_vertical_gap_mm": lowest - max(b.max.Z for b in boxes.values()),
                              "surface_intersections": hits, "clear_of_surface_intersections": not hits}
    print(d, json.dumps(out["results"][str(d)]), flush=True)
(ROOT / "reviews" / "pylon_lowering_verification.json").write_text(json.dumps(out, indent=1))
