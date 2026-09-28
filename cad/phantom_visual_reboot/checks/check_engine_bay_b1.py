"""Rough-study checks for engine-bay concept B1 (visual concept only; not an approval).

1. Engine parts inside the union of: existing bay box, proposed forward pocket, R1 stub/connector/liner voids.
   Pylons / pipe struts are attachment stand-ins that embed into walls and are reported separately.
2. Main-ramp interference (deployed + stowed) against engine parts and door (both poses), intersection volume.
3. Door open/closed contained in bay+pocket.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import aft_exhaust_r1 as aft
import engine_read_study as e
import engine_bay_study as b
from cadgen import build123d as bd, read_step

ROOT = Path(__file__).resolve().parents[1]

def leaves(n):
    c = list(getattr(n, "children", ()) or ())
    return [l for k in c for l in leaves(k)] if c else [n]

bay = bd.Box(b.BAY_X[1] - b.BAY_X[0], 2 * b.BAY_HALF_Y, b.BAY_Z[1] - b.BAY_Z[0]).translate(
    ((b.BAY_X[0] + b.BAY_X[1]) / 2, 0, (b.BAY_Z[0] + b.BAY_Z[1]) / 2))
void = (bay + b.pocket_cutter() + aft.inner_liner_tool() + aft.connector_cutter() + aft.ruled_loft(e.STUB_SECTIONS)).clean()

def outside(p):
    inter = p & void
    return p.volume - (sum(s.volume for s in inter.solids()) if inter is not None else 0.0)

def overlap(a, c):
    inter = a & c
    return 0.0 if inter is None else sum(s.volume for s in inter.solids())

rep = {"engine": {}, "door": {}, "ramp_overlap_mm3": {}}
engine = b.engine_parts()
mount = lambda l: "pylon" in l or "strut" in l
bad = []
for p in engine:
    o = outside(p)
    rep["engine"][p.label] = round(max(o, 0), 2)
    if not mount(p.label) and o > 0.5:
        bad.append((p.label, round(o, 2)))
rep["engine_non_mount_outside_gt_0.5mm3"] = bad
for pose in (False, True):
    d = b.door_part(pose)
    rep["door"][d.label] = round(max(outside(d), 0), 2)

ramps = {}
for state in ("Stowed", "Deployed"):
    for l in leaves(read_step(str(ROOT / "STEP" / f"S_AftExhaust_R1_{state}.step"))):
        if str(l.label).startswith("intake_r1_ramp"):
            ramps[state] = l
for state, r in ramps.items():
    bb = r.bounding_box()
    rep["ramp_bbox_" + state] = [round(v, 2) for v in (bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z)]
    worst = 0.0
    for p in engine:
        pb = p.bounding_box()
        if pb.max.X < bb.min.X or pb.min.X > bb.max.X or pb.max.Z < bb.min.Z or pb.min.Z > bb.max.Z:
            continue
        worst = max(worst, overlap(p, r))
    rep["ramp_overlap_mm3"]["engine_vs_" + state] = round(worst, 3)
    for pose in (False, True):
        d = b.door_part(pose)
        rep["ramp_overlap_mm3"][f"{d.label}_vs_{state}"] = round(overlap(d, r), 3)
out = ROOT / "reviews" / "engine_bay_b1_checks.json"
out.write_text(json.dumps(rep, indent=1))
print(json.dumps({k: v for k, v in rep.items() if k != "engine"}, indent=1))
print("non-mount engine parts outside void:", bad)
