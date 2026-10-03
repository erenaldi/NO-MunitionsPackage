"""Independent saved-artifact check for the R20 F07 main-fin root seats.

Reads the saved R20 STEP + sidecar + metadata, and the saved R19 STEP +
sidecar + metadata (main checkout, read-only) as the reference. Does not
import the R20 builder. Writes reviews/halberd_r20_fin_seats_checks.json.
"""
import json
import math
import os
import re
import sys
from pathlib import Path

from cadgen import build123d as bd, read_scene

ROOT = Path(__file__).resolve().parents[1]
R20 = ROOT / "STEP" / "halberd_r20_fin_seats.step"
META = ROOT / "reviews" / "halberd_r20_fin_seats.json"
REPORT = ROOT / "reviews" / "halberd_r20_fin_seats_checks.json"
R19_DIR = Path(os.environ.get(
    "R19_SAVED_DIR",
    r"C:\Users\erena\Desktop\Nuclear Option Munitions Package\cad\halberd_rounded_square"))
R19 = R19_DIR / "STEP" / "halberd_r19_surface.step"
R19_META = R19_DIR / "reviews" / "halberd_r19_surface.json"
HOST = "main_body_intake_r12"
HW_GROUP, COVER_GROUP = "r19_surface_hardware", "r20_fin_seat_covers"
FINS = {"1": ("main_fin_1", 45.0), "2": ("main_fin_2", 135.0),
        "3": ("main_fin_3", 225.0), "4": ("main_fin_4", 315.0)}
CLEARANCE = 2.0
TOL = 1e-4
MAX_POCKET_DEPTH = 0.8
failures, notes = [], {}


def fail(message):
    failures.append(message)


def leaves(path):
    scene = read_scene(path)
    rows = tuple(scene.leaves())
    parts = {row.label: scene.resolve(row.ref).shape() for row in rows}
    if len(parts) != len(rows):
        fail(f"{path.name}: duplicate leaf labels")
    return scene, rows, parts


def precise_volume(shape):
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    total = 0.0
    for solid in shape.solids():
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(solid.wrapped, props, 1e-9, True, True)
        total += props.Mass()
    return total


def closed_and_clean(shape):
    """Every shell closed, and BRepAlgoAPI_Check (incl. self-intersection) passes."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
    closed = all(BRep_Tool.IsClosed_s(s.wrapped) for s in shape.shells())
    check = BRepAlgoAPI_Check(shape.wrapped, True, True)
    return closed, check.IsValid()


def ray_skin(shape, point, outward, start=20.0):
    """Outermost crossing of `shape` on the line through point along -outward."""
    from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
    from OCP.gce import gce_MakeLin
    origin = point + outward * start
    hits = BRepIntCurveSurface_Inter()
    hits.Init(shape.wrapped, gce_MakeLin(bd.Axis(origin, -outward).wrapped).Value(), 1e-7)
    ws = []
    while hits.More():
        if hits.W() >= 0.0:
            ws.append(hits.W())
        hits.Next()
    if not ws:
        raise ValueError("reference skin ray missed")
    return origin - outward * min(ws)


def boxes_near(a, b, margin):
    ba, bb = a.bounding_box(), b.bounding_box()
    return not (ba.min.X - margin > bb.max.X or bb.min.X - margin > ba.max.X or
                ba.min.Y - margin > bb.max.Y or bb.min.Y - margin > ba.max.Y or
                ba.min.Z - margin > bb.max.Z or bb.min.Z - margin > ba.max.Z)


def frame(clock):
    a = math.radians(clock)
    return bd.Vector(0, math.sin(a), math.cos(a)), bd.Vector(0, math.cos(a), -math.sin(a))


scene20, rows20, parts = leaves(R20)
scene19, rows19, ref = leaves(R19)
meta = json.loads(META.read_text(encoding="utf-8"))
meta19 = json.loads(R19_META.read_text(encoding="utf-8"))
if meta.get("source_document_hash") != scene19.document_hash:
    fail("R20 metadata source hash != saved R19 document hash")

# 1. Composition: all R19 leaves present; new leaves are exactly 8 covers + 16 heads.
missing = sorted(set(ref) - set(parts))
if missing:
    fail(f"R19 leaves missing: {missing[:5]}")
new = set(parts) - set(ref)
covers = sorted(l for l in new if re.fullmatch(r"main_r20_F07_[1-4][pm]_cover", l))
heads = sorted(l for l in new if re.fullmatch(r"main_r20_F07_[1-4][pm]_fastener_[12]", l))
if new != set(covers) | set(heads):
    fail(f"unexpected new leaves: {sorted(new - set(covers) - set(heads))[:5]}")
if set(covers) != set(meta["cover_labels"]) or set(heads) != set(meta["hardware_labels"]):
    fail("new leaves do not match metadata labels")
if len(covers) != 8 or len(heads) != 16:
    fail(f"expected 8 seats / 16 heads, found {len(covers)} / {len(heads)}")
seat_ids = sorted(l[:-len("_cover")] for l in covers)
for sid in seat_ids:
    n = sum(1 for h in heads if h.startswith(sid + "_fastener_"))
    if n != 2:
        fail(f"{sid}: {n} heads, expected 2")

# 2. Validity of every leaf; new parts closed and free of self-intersection.
for label, part in parts.items():
    if not part.is_valid or len(part.solids()) != 1 or part.volume <= 1e-8:
        fail(f"{label}: invalid, empty or not one solid")
for label in sorted(new):
    closed, clean = closed_and_clean(parts[label])
    if not closed or not clean:
        fail(f"{label}: closed={closed} BRepAlgoAPI_Check={clean}")

# 3. Retained R19 parts unchanged (all but the main host).
for label, part in ref.items():
    if label == HOST or label not in parts:
        continue
    other = parts[label]
    if abs(part.volume - other.volume) > 1e-6 or \
            (part.center() - other.center()).length > 1e-6:
        fail(f"{label}: retained R19 part changed")

# 4. Host: no material gained; removed material only at the 8 seats.
host19, host20 = ref[HOST], parts[HOST]
gain = host20 - host19
gained = precise_volume(gain) if gain else 0.0
if gained > 1e-3:
    fail(f"{HOST}: gained {gained:.5f} mm3")
removed_shape = host19 - host20
removed_solids = removed_shape.solids() if removed_shape else []
seat_origin = {sid: bd.Vector(*meta["seats"][sid]["frame_origin_mm"]) for sid in seat_ids}
per_seat = {sid: [] for sid in seat_ids}
for solid in removed_solids:
    c = solid.center()
    sid, d = min(((s, (c - o).length) for s, o in seat_origin.items()), key=lambda r: r[1])
    box = solid.bounding_box()
    if d > 20.0 or box.min.X < -981.0 or box.max.X > -959.0:
        fail(f"removed material outside the seats at {tuple(round(v, 2) for v in c)}")
        continue
    per_seat[sid].append(solid)
removed_total = sum(precise_volume(s) for s in removed_solids)
volume_delta = host19.volume - host20.volume
if abs(removed_total - meta["host_volume_removed_mm3"]) > max(5e-3, 1e-4 * removed_total):
    fail(f"removed {removed_total:.4f} != metadata {meta['host_volume_removed_mm3']:.4f}")
seat_report = {}
for sid in seat_ids:
    vol = sum(precise_volume(s) for s in per_seat[sid])
    seat_report[sid] = {"removed_mm3": vol}
    if vol <= 1e-3:
        fail(f"{sid}: no host material removed")
    elif abs(vol - meta["seats"][sid]["removed_mm3"]) > max(5e-3, 1e-4 * vol):
        fail(f"{sid}: removed {vol:.4f} != metadata {meta['seats'][sid]['removed_mm3']:.4f}")

# 5. Pocket depth / cover setback probes on the land and on the outer facet.
for sid in seat_ids:
    s = meta["seats"][sid]
    world = [bd.Vector(*p) for p in s["outline_world_mm"]]
    fin_label, _ = FINS[sid[-2]]
    mid = [p for p in world if abs(p.X - s["center_x_mm"]) < 0.6]
    fin_c = ref[fin_label].center()
    near_fin = lambda p: (p - bd.Vector(p.X, fin_c.Y, fin_c.Z)).length
    inner, outer = min(mid, key=near_fin), max(mid, key=near_fin)
    crease = bd.Vector(*s["frame_origin_mm"])
    cover = parts[f"{sid}_cover"]
    for name, a, b, n in (("land", inner, crease, s["land_normal"]),
                          ("facet", crease, outer, s["facet_normal"])):
        n = bd.Vector(*n).normalized()
        probe = a + (b - a) * 0.4
        skin = ray_skin(host19, probe, n)
        if (skin - probe).length > 0.05:
            fail(f"{sid} {name}: probe is not on the R19 skin ({(skin - probe).length:.3f})")
        open_ = not host20.is_inside(skin - n * 0.3)
        floor = host20.is_inside(skin - n * (MAX_POCKET_DEPTH - 0.05))
        under = host20.is_inside(skin - n * 0.5)
        cov_in = cover.is_inside(skin - n * 0.4)
        cov_set = not cover.is_inside(skin - n * 0.1) and not host20.is_inside(skin - n * 0.1)
        seat_report[sid][name] = {"open_0.3": open_, "floor_before_0.75": floor,
                                  "no_host_at_0.5": not under, "cover_at_0.4": cov_in,
                                  "clear_at_0.1": cov_set}
        if not (open_ and floor and not under and cov_in and cov_set):
            fail(f"{sid} {name}: pocket/cover probe failed {seat_report[sid][name]}")

# 6. Hardware: groups, no overlap, heads clear of the host interior.
groups = {child.label: child for child in scene20.roots[0].children}


def group_labels(name):
    node = groups.get(name)
    return {c.label for c in node.children} if node else set()


if not set(heads) <= group_labels(HW_GROUP):
    fail("R20 heads are not in the metal hardware group")
if set(covers) != group_labels(COVER_GROUP):
    fail("R20 covers are not exactly the cover group")
r19_groups = {c.label: {g.label for g in c.children} for c in scene19.roots[0].children if c.children}
if not r19_groups.get(HW_GROUP, set()) <= group_labels(HW_GROUP):
    fail("R19 hardware group lost members")
for label in heads:
    head = parts[label]
    if host20.is_inside(head.center()):
        fail(f"{label}: centre inside host")
    for other_label in (HOST, f"{label.rsplit('_fastener_', 1)[0]}_cover"):
        inter = head & parts[other_label]
        if inter and inter.volume > TOL:
            fail(f"{label}: overlaps {other_label} by {inter.volume:.5f} mm3")
for label in covers:
    inter = parts[label] & host20
    if inter and inter.volume > TOL:
        fail(f"{label}: overlaps host by {inter.volume:.5f} mm3")

# 7. Clearance >= 2 mm: visible fin roots, all other R19 detail leaves, seams,
# R19 engraved panel outlines, and the other seats.
visible = {k: ref[l] - host19 for k, (l, _) in FINS.items()}
details = [p for l, p in ref.items() if l != HOST and not l.startswith("main_fin_")]
seams = [(k, v["x_mm"][0], v["x_mm"][1]) for k, v in meta19["seams"].items()]
panel_pts = []
for item in meta19["plan"]:
    if item["stage"] != "main" or item["kind"] not in ("rect", "round", "louvre") or \
            abs(item["x"] + 970.0) > 200.0:
        continue
    radial, tangent = frame(item["clock"])
    hl, hw = item["length"] / 2.0, item["width"] / 2.0
    if item["kind"] == "round":
        offs = [(hl * math.cos(a / 18 * math.pi), hl * math.sin(a / 18 * math.pi)) for a in range(36)]
    else:
        offs = [(hl * s / 10, side * hw) for s in range(-10, 11) for side in (-1, 1)] + \
               [(side * hl, hw * s / 5) for s in range(-5, 6) for side in (-1, 1)]
    for dx, dt in offs:
        base = bd.Vector(item["x"] + dx, 0, 0) + tangent * (item["tangent"] + dt)
        try:
            panel_pts.append((item["id"], ray_skin(host19, base + radial * 200.0, radial, 100.0)))
        except ValueError:
            pass
clear_report = {}
seat_parts = {}
for sid in seat_ids:
    pieces = per_seat[sid] + [parts[f"{sid}_cover"]] + \
        [parts[h] for h in heads if h.startswith(sid + "_fastener_")]
    seat_parts[sid] = pieces
    fin_gap = min(p.distance_to(visible[sid[-2]]) for p in pieces)
    other_gap, other_label = math.inf, None
    for d in details:
        for p in pieces:
            if boxes_near(p, d, CLEARANCE + 1.0):
                dist = p.distance_to(d)
                if dist < other_gap:
                    other_gap, other_label = dist, d.label
    for k, vis in visible.items():
        if k != sid[-2]:
            other_gap = min(other_gap, min(p.distance_to(vis) for p in pieces))
    xs = [p.bounding_box() for p in pieces]
    x0, x1 = min(b.min.X for b in xs), max(b.max.X for b in xs)
    seam_gap = min(0.0 if a <= x1 and b >= x0 else min(abs(x0 - b), abs(a - x1))
                   for _, a, b in seams)
    panel_gap = min((min(p.distance_to(pt) for p in pieces) - 0.2 for _, pt in panel_pts),
                    default=math.inf)
    clear_report[sid] = {"visible_fin_mm": fin_gap, "nearest_detail_mm": other_gap,
                         "nearest_detail": other_label, "seam_axial_mm": seam_gap,
                         "panel_outline_mm": panel_gap}
    for name, value in (("visible fin root", fin_gap), ("detail", other_gap),
                        ("seam", seam_gap), ("panel outline", panel_gap)):
        if value < CLEARANCE - 1e-6:
            fail(f"{sid}: {value:.3f} mm to {name} < {CLEARANCE}")
for i, a in enumerate(seat_ids):
    for b in seat_ids[i + 1:]:
        if any(boxes_near(p, q, CLEARANCE) and p.distance_to(q) < CLEARANCE
               for p in seat_parts[a] for q in seat_parts[b]):
            fail(f"seats {a}/{b} closer than {CLEARANCE} mm")

# 8. Sidecar: heads metal, covers paint, R19 leaves keep their materials.
side20 = json.loads(R20.with_suffix(".step.json").read_text(encoding="utf-8"))
side19 = json.loads(R19.with_suffix(".step.json").read_text(encoding="utf-8"))
if side20.get("documentHash") != scene20.document_hash:
    fail("R20 sidecar hash does not match the saved STEP")
ap20, ap19 = side20["appearance"], side19["appearance"]
occ20 = {r.label: r.ref.split("#")[-1] for r in rows20}
occ19 = {r.label: r.ref.split("#")[-1] for r in rows19}


def material_name(ap, occ):
    key = ap["assignments"].get(occ) if occ else None
    return ap["materials"].get(key, {}).get("name") if key else None


for label in sorted(new):
    want = "Service cover paint" if label in covers else "Small metallic hardware"
    got = material_name(ap20, occ20[label])
    if got != want:
        fail(f"{label}: material {got}, expected {want}")
changed = [l for l in ref if material_name(ap19, occ19[l]) != material_name(ap20, occ20.get(l))]
if changed:
    fail(f"R19 leaves changed material: {changed[:5]}")

report = {
    "status": "PASS" if not failures else "FAIL",
    "failures": failures[:60],
    "failure_count": len(failures),
    "document_hash": scene20.document_hash,
    "reference_r19_hash": scene19.document_hash,
    "leaves": len(parts), "r19_leaves": len(ref),
    "seats": len(covers), "heads": len(heads),
    "host_gain_mm3": gained,
    "host_removed_mm3": removed_total, "host_volume_delta_mm3": volume_delta,
    "removed_solids": len(removed_solids),
    "per_seat": seat_report,
    "clearance_mm": clear_report,
    "panel_outline_points_checked": len(panel_pts),
}
REPORT.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("status", "failure_count", "failures", "seats",
                                         "heads", "host_gain_mm3", "host_removed_mm3",
                                         "removed_solids")}, indent=1, default=float))
sys.exit(0 if not failures else 1)
