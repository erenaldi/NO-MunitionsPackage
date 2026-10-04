"""Saved-artifact check for the R24p F11 fairing-lip folded seats (booster_fin_fairing_1 only).

Reads the saved R23p STEP + sidecar + metadata and the saved R20 STEP (reference).
Does not import the builder. The host is the 12-face fin leaf, so its removed/gained
volume pair runs on the whole leaf; validity and probes run on a local crop.
Unchanged leaves: equal default volume (1e-6) or, failing that, equal PRECISE volume
within 0.01 mm3 (cadgen 0.7.10 re-saved leaves differ ~0.004 mm3 at default precision),
plus bounding box within 1e-6 mm.
Writes reviews/halberd_r24p_flank_lip_seats_check.json.
"""
import json
import re
import sys
from pathlib import Path

from cadgen import build123d as bd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from check_kit import (Report, Stages, box_around, closed_and_clean, crop_shape,  # noqa: E402
                       load_leaves, min_distance, precise_volume, ray_skin, removed_volume)
from surface_detail import _ray_hits  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R23 = ROOT / "STEP" / "r24p_flank_seats.step"
R20 = ROOT / "STEP" / "halberd_r20_fin_seats.step"
META = ROOT / "reviews" / "halberd_r24p_flank_lip_seats.json"
OUT = ROOT / "reviews" / "halberd_r24p_flank_lip_seats_check.json"
FIN = "booster_fin_fairing_1"
HW_GROUP, COVER_GROUP = "r19_surface_hardware", "r24p_lip_seat_covers"
SEAT_X = (-1251.0, -1213.0)       # 24 mm seat + chamfer/countersink margin
CLEARANCE, TOL, VOL_TOL = 2.0, 1e-4, 0.01
TAN45 = bd.Vector(0, 0.7071067811865476, -0.7071067811865476)

st = Stages(stage_budget_s=120.0, total_budget_s=175.0)
rep = Report()
scene23, rows23, parts = load_leaves(R23, rep)
scene20, rows20, ref = load_leaves(R20, rep)
meta = json.loads(META.read_text(encoding="utf-8"))
if meta.get("source_document_hash") != scene20.document_hash:
    rep.fail("metadata source hash != saved R20 document hash")
st.stage("composition")

new = set(parts) - set(ref)
covers = sorted(l for l in new if re.fullmatch(r"booster_r24p_F11_1[pm]_cover", l))
heads = sorted(l for l in new if re.fullmatch(r"booster_r24p_F11_1[pm]_fastener_[12]", l))
if new != set(covers) | set(heads):
    rep.fail(f"unexpected new leaves {sorted(new - set(covers) - set(heads))}")
if len(covers) != 2 or len(heads) != 4:
    rep.fail(f"expected 2 seats / 4 heads, found {len(covers)} / {len(heads)}")
seat_ids = [c[:-len("_cover")] for c in covers]
heads_per_seat = {s: sum(h.startswith(s + "_fastener_") for h in heads) for s in seat_ids}
for s, n in heads_per_seat.items():
    if n != 2:
        rep.fail(f"{s}: {n} heads")
st.stage("unchanged_leaves")

unchanged_bad, precise_used = [], {}
for label, a in ref.items():
    if label == FIN:
        continue
    b = parts.get(label)
    if b is None:
        unchanged_bad.append((label, "missing"))
        continue
    if abs(a.volume - b.volume) > 1e-6:
        dv = abs(precise_volume(a) - precise_volume(b))
        precise_used[label] = dv
        if dv > VOL_TOL:
            unchanged_bad.append((label, f"precise volume changed by {dv:.5f}"))
            continue
    ba, bb = a.bounding_box(), b.bounding_box()
    if any(abs(u - v) > 1e-6 for u, v in zip(
            (ba.min.X, ba.min.Y, ba.min.Z, ba.max.X, ba.max.Y, ba.max.Z),
            (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z))):
        unchanged_bad.append((label, "bbox changed"))
    st.check()
for label, reason in unchanged_bad:
    rep.fail(f"{label}: {reason}")
st.stage("new_parts_valid")

new_valid = {}
for label in sorted(new):
    p = parts[label]
    closed, clean = closed_and_clean(p)
    new_valid[label] = {"valid": p.is_valid, "solids": len(p.solids()), "closed": closed,
                        "check": clean, "volume_mm3": precise_volume(p), "faces": len(p.faces())}
    if not (p.is_valid and len(p.solids()) == 1 and closed and clean and p.volume > 1e-6):
        rep.fail(f"{label}: invalid {new_valid[label]}")
st.stage("host_volumes")

f20, f23 = ref[FIN], parts[FIN]
removed, gained = removed_volume(f20, f23)
lost_shape = f20 - f23
lost_solids = lost_shape.solids() if lost_shape else []
for s in lost_solids:
    bb = s.bounding_box()
    if bb.min.X < SEAT_X[0] or bb.max.X > SEAT_X[1]:
        rep.fail(f"removed material outside the seat window at X {bb.min.X:.1f}..{bb.max.X:.1f}")
if removed <= 1e-3:
    rep.fail(f"{FIN} removed volume {removed:.6f} mm3 is not > 0")
if gained > 1e-6:
    rep.fail(f"{FIN} gained {gained:.6f} mm3")
if abs(removed - meta["host_volume_removed_mm3"]) > max(5e-3, 1e-4 * removed):
    rep.fail(f"removed {removed:.4f} != metadata {meta['host_volume_removed_mm3']:.4f}")


def side_of(shape, sid):
    c = shape.center()
    return (c - bd.Vector(c.X, 0, 0)).dot(TAN45 * meta["seats"][sid]["tangent_sign"]) > 0


per_seat = {}
for sid in seat_ids:
    mine = [s for s in lost_solids if side_of(s, sid)]
    per_seat[sid] = {"removed_mm3": sum(precise_volume(s) for s in mine), "solids": len(mine)}
    if per_seat[sid]["removed_mm3"] <= 1e-3:
        rep.fail(f"{sid}: removed no host material")
st.stage("local_crop_validity")

box = box_around(SEAT_X[0] - 2.0, SEAT_X[1] + 2.0)
crop23 = crop_shape(f23, box)
crop20 = crop_shape(f20, box)
c_closed, c_clean = closed_and_clean(crop23)
if not (crop23.is_valid and c_closed and c_clean):
    rep.fail(f"fin crop invalid: valid={crop23.is_valid} closed={c_closed} check={c_clean}")
st.stage("probes")

probes, skin_faces, head_to_lip = {}, [], {}
for sid in seat_ids:
    m = meta["seats"][sid]
    cover = parts[f"{sid}_cover"]
    rows, faces = {}, {}
    for pr in m["probes"]:          # ledge strip + flank sites, each along its own skin normal
        name = pr["name"]
        p0, n = bd.Vector(*pr["point_mm"]), bd.Vector(*pr["normal"]).normalized()
        faces[name] = _ray_hits(crop20, p0 + n * 20.0, -n)[0][2]
        skin = ray_skin(crop20, p0, n)
        r = {"open_0.3": not crop23.is_inside(skin - n * 0.3),
             "floor_0.75": crop23.is_inside(skin - n * 0.75),
             "no_host_0.5": not crop23.is_inside(skin - n * 0.5),
             "cover_0.4": cover.is_inside(skin - n * 0.4),
             "clear_0.1": not cover.is_inside(skin - n * 0.1) and not crop23.is_inside(skin - n * 0.1)}
        rows[name] = r
        if not all(r.values()):
            rep.fail(f"{sid} {name}: pocket/cover probe {r}")
    probes[sid] = rows
    ledge, flank = faces["ledge_fwd"], faces["flank_mid"]
    if ledge.is_same(flank):
        rep.fail(f"{sid}: ledge and flank probes landed on one face (no fold)")
    skin_faces += [ledge, flank]
    head_to_lip[sid] = [min_distance([bd.Vector(*s["point_mm"])], [ledge])
                        for s in m["screw_sites"]]
    for d in head_to_lip[sid]:
        if d < 2.4 - 1e-3:
            rep.fail(f"{sid}: head centre {d:.3f} mm from the lip < 2.4")
    for h in [x for x in heads if x.startswith(sid)]:
        head = parts[h]
        if crop23.is_inside(head.center()):
            rep.fail(f"{h}: centre inside host")
        for other in (crop23, cover):
            inter = head & other
            if inter and inter.volume > TOL:
                rep.fail(f"{h}: overlaps by {inter.volume:.5f} mm3")
    inter = cover & crop23
    if inter and inter.volume > TOL:
        rep.fail(f"{sid}_cover overlaps host by {inter.volume:.5f} mm3")
st.stage("clearance")

fin_other = [f for f in crop20.faces() if not any(f.is_same(g) for g in skin_faces)]
clear = {}
for sid in seat_ids:
    pieces = [s for s in lost_solids if side_of(s, sid)]
    pieces += [parts[f"{sid}_cover"]] + [parts[h] for h in heads if h.startswith(sid)]
    others = [p for l, p in parts.items() if l != FIN and not l.startswith(sid)]
    clear[sid] = {"fin_crease_ledge_blade_mm": min_distance(pieces, fin_other),
                  "other_leaves_incl_body_and_other_seat_mm": min_distance(pieces, others)}
    for k, v in clear[sid].items():
        if v < CLEARANCE - 1e-6:
            rep.fail(f"{sid}: {k} = {v:.3f} < {CLEARANCE}")
st.stage("groups_materials")

groups = {c.label: {g.label for g in c.children} for c in scene23.roots[0].children}
if not set(heads) <= groups.get(HW_GROUP, set()):
    rep.fail("heads not in the metal hardware group")
if set(covers) != groups.get(COVER_GROUP, set()):
    rep.fail("covers are not exactly the cover group")
side = json.loads(R23.with_suffix(".step.json").read_text(encoding="utf-8"))
if side.get("documentHash") != scene23.document_hash:
    rep.fail("sidecar hash does not match the saved STEP")
ap = side["appearance"]
occ = {r.label: r.ref.split("#")[-1] for r in rows23}
mat = lambda l: ap["materials"].get(ap["assignments"].get(occ[l], ""), {}).get("name")
for l in sorted(new):
    want = "Service cover paint" if l in covers else "Small metallic hardware"
    if mat(l) != want:
        rep.fail(f"{l}: material {mat(l)} != {want}")
timings = st.done()

report = {"status": "PASS" if not rep.failures else "FAIL", "failures": rep.failures,
          "document_hash": scene23.document_hash, "reference_r20_hash": scene20.document_hash,
          "leaves": len(parts), "r20_leaves": len(ref), "new_leaves": sorted(new),
          "heads_per_seat": heads_per_seat, "unchanged_failures": unchanged_bad,
          "precise_volume_rechecks_mm3": precise_used,
          "new_parts": new_valid, "fin_removed_mm3": removed, "fin_gained_mm3": gained,
          "removed_solids": len(lost_solids), "per_seat": per_seat,
          "fin_faces": [len(f20.faces()), len(f23.faces())],
          "crop_faces": [len(crop20.faces()), len(crop23.faces())],
          "probes": probes, "head_centre_to_lip_mm": head_to_lip,
          "clearance_mm": clear, "stage_seconds": timings}
OUT.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("status", "failures", "heads_per_seat", "fin_removed_mm3",
                                         "fin_gained_mm3", "per_seat", "clearance_mm", "fin_faces",
                                         "precise_volume_rechecks_mm3")}, indent=1, default=float))
sys.exit(rep.exit_code())
