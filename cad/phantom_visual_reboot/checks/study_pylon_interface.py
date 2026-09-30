"""Mounting-interface STUDY (read-only): how much of the actual donor pylon surface overlaps each dorsal candidate part,
as height maps in the unchanged donor frame (CAD mm; +Z dorsal).  Nothing is modified; nothing is a fit approval.

For every candidate leaf with material above Z=40 the top/bottom surface heights are rasterised on a 2 mm XY grid from the
saved B2H Stowed tessellation; the pylon's lowest surface height per cell comes from reference/agm1_mount/pylon_candidate_frame.json.
Required lowering at a cell = candidate top - pylon lowest surface.  Reported per leaf and for hybrid (lower d + relief) options.
Height maps are approximations from tessellation (0.1 mm chord tol) and treat each leaf as one height column; they are bounds for
option comparison, not a substitute for the final surface/solid fit check.
"""
import json
from pathlib import Path
import numpy as np
from cadgen import read_scene

ROOT = Path(__file__).resolve().parents[1]
GRID = 2.0
PYLON = json.loads((ROOT / "reference/agm1_mount/pylon_candidate_frame.json").read_text(encoding="utf-8"))
pv = np.array(PYLON["vertices_CAD_mm"], float)
ptri = np.array(PYLON["triangles"], int)
x0, x1 = pv[:, 0].min() - 2, pv[:, 0].max() + 2
y0, y1 = pv[:, 1].min() - 2, pv[:, 1].max() + 2
xs = np.arange(x0, x1, GRID)
ys = np.arange(y0, y1, GRID)
NX, NY = len(xs), len(ys)


def raster(verts, tris, mode):
    """Height map (NY, NX): 'max' or 'min' z of the triangles over each cell centre; NaN where empty."""
    out = np.full((NY, NX), np.nan)
    for t in tris:
        a, b, c = verts[t[0]], verts[t[1]], verts[t[2]]
        lox, hix = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
        loy, hiy = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
        if hix < x0 or lox > x1 or hiy < y0 or loy > y1:
            continue
        i0 = max(int(np.floor((lox - x0) / GRID)), 0); i1 = min(int(np.ceil((hix - x0) / GRID)), NX - 1)
        j0 = max(int(np.floor((loy - y0) / GRID)), 0); j1 = min(int(np.ceil((hiy - y0) / GRID)), NY - 1)
        if i1 < i0 or j1 < j0:
            continue
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(xs[i0:i1 + 1], ys[j0:j1 + 1])
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        if not inside.any():
            continue
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        sub = out[j0:j1 + 1, i0:i1 + 1]
        cur = np.where(inside, z, np.nan)
        if mode == "max":
            sub[:] = np.fmax(sub, cur)
        else:
            sub[:] = np.fmin(sub, cur)
    return out


pyl_low = raster(pv, ptri, "min")
scene = read_scene(str(ROOT / "STEP" / "S_EngineBay_B2H_Stowed_Full.step"))
leaves = {str(o.label): o.shape() for o in scene.leaves()}
res = {"grid_mm": GRID, "pylon_lowest_surface_z_min_mm": float(np.nanmin(pyl_low)), "leaves": {}}
allmax = np.full((NY, NX), -1e9)
delta_by_leaf = {}
for name, shape in leaves.items():
    bb = shape.bounding_box(optimal=False)
    if bb.max.Z < 40.0 or bb.max.X < x0 or bb.min.X > x1:
        continue
    verts, tris = shape.tessellate(0.1, 0.1)
    V = np.array([[v.X, v.Y, v.Z] for v in verts], float)
    T = np.array(tris, int)
    top = raster(V, T, "max")
    bot = raster(V, T, "min")
    delta = top - pyl_low                         # >0 where the candidate top pokes above the pylon underside
    mask = np.isfinite(delta) & (delta > 0)
    if not mask.any():
        continue
    cells = int(mask.sum())
    j, i = np.unravel_index(np.nanargmax(np.where(mask, delta, -1e9)), delta.shape)
    thick = (top - bot)[mask]
    res["leaves"][name] = {
        "cells_over_pylon_underside": cells, "footprint_area_mm2": cells * GRID * GRID,
        "max_required_lowering_mm": float(delta[mask].max()),
        "worst_cell_xy_mm": [float(xs[i]), float(ys[j])],
        "column_thickness_at_worst_cell_mm": float((top - bot)[j, i]),
        "median_required_lowering_mm": float(np.median(delta[mask])),
        "mean_column_thickness_over_footprint_mm": float(thick.mean()),
    }
    delta_by_leaf[name] = np.where(mask, delta, 0.0)
    allmax = np.fmax(allmax, np.where(np.isfinite(top), top, -1e9))
total = np.where(np.isfinite(pyl_low), allmax - pyl_low, -1e9)
res["overall_max_required_lowering_mm"] = float(total.max())
# hybrid: lower by d, then residual intrusion per leaf must be shaved from that leaf
hyb = {}
for d in (0, 2, 4, 6, 8, 9.5, 10.5):
    row = {}
    for name, dl in delta_by_leaf.items():
        resid = np.clip(dl - d, 0, None)
        if resid.max() > 0:
            row[name] = {"max_residual_intrusion_mm": float(resid.max()), "residual_area_mm2": float((resid > 0).sum() * GRID * GRID),
                         "residual_volume_mm3_upper_bound": float(resid.sum() * GRID * GRID)}
    hyb[str(d)] = row
res["hybrid_lowering_then_relief"] = hyb
(ROOT / "reviews" / "pylon_interface_study.json").write_text(json.dumps(res, indent=1))
print(json.dumps({"overall_max_required_lowering_mm": res["overall_max_required_lowering_mm"], "leaves": res["leaves"]}, indent=1))
