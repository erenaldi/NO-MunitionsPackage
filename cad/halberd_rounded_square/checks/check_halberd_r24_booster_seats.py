"""Saved-artifact check for R24: R24p folded lip seats rolled out to booster_fin_fairing_2/3/4.

Reads the saved R24 STEP + sidecar + metadata and the saved R24p STEP (reference, which
already holds fin 1 and its two seats). Does not import the builder.
- Unchanged leaves (every R24p leaf except fins 2-4, so fin 1 and its seats included):
  equal default volume (1e-6) or, failing that, equal PRECISE volume within 0.01 mm3
  (cadgen 0.7.10 re-saved leaves differ ~0.004 mm3 at default precision), plus bbox 1e-6.
- Each changed fin is a 12-face leaf: precise removed/gained pair on the whole leaf.
- Validity, probes and clearances run per fin on local crops. For clearance to other
  leaves, each other leaf is clipped to the seat's bounding box grown by MARGIN; a
  distance below MARGIN to the clip equals the true distance (the nearest point lies in
  the grown box), and a clip result >= MARGIN proves the true distance >= MARGIN > 2.
Writes reviews/halberd_r24_booster_seats_check.json.
"""
import json
import re
import sys
from pathlib import Path

from cadgen import build123d as bd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from check_kit import (Report, Stages, box_around, boxes_near, closed_and_clean, crop_shape, frame,  # noqa: E402
                       load_leaves, min_distance, precise_volume, ray_skin, removed_volume)
from surface_detail import _ray_hits  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R24 = ROOT / "STEP" / "r24_booster_seats.step"
R24P = ROOT / "STEP" / "r24p_flank_seats.step"
META = ROOT / "reviews" / "halberd_r24_booster_seats.json"
OUT = ROOT / "reviews" / "halberd_r24_booster_seats_check.json"
FINS = {"booster_fin_fairing_2": (2, 135.0), "booster_fin_fairing_3": (3, 225.0),
        "booster_fin_fairing_4": (4, 315.0)}
HW_GROUP, COVER_GROUP = "r19_surface_hardware", "r24_lip_seat_covers"
SEAT_X = (-1251.0, -1213.0)       # 24 mm seat + chamfer/countersink margin
CLEARANCE, TOL, VOL_TOL, MARGIN = 2.0, 1e-4, 0.01, 5.0
COVER_RE = r"booster_r24p?_F11_[1-4][pm]_cover"
HEAD_RE = r"booster_r24p?_F11_[1-4][pm]_fastener_[12]"

st = Stages(stage_budget_s=120.0, total_budget_s=178.0)
rep = Report()
scene24, rows24, parts = load_leaves(R24, rep)
scene_p, rows_p, ref = load_leaves(R24P, rep)
meta = json.loads(META.read_text(encoding="utf-8"))
if meta.get("source_document_hash") != scene_p.document_hash:
    rep.fail("metadata source hash != saved R24p document hash")
st.stage("composition")

new = set(parts) - set(ref)
covers = sorted(l for l in parts if re.fullmatch(COVER_RE, l))
heads = sorted(l for l in parts if re.fullmatch(HEAD_RE, l))
new_covers = [c for c in covers if c in new]
new_heads = [h for h in heads if h in new]
if new != set(new_covers) | set(new_heads):
    rep.fail(f"unexpected new leaves {sorted(new - set(new_covers) - set(new_heads))}")
if len(covers) != 8 or len(heads) != 16 or len(new_covers) != 6 or len(new_heads) != 12:
    rep.fail(f"expected 8 seats / 16 heads (6 / 12 new), found {len(covers)} / {len(heads)} "
             f"({len(new_covers)} / {len(new_heads)} new)")
seat_ids = [c[:-len("_cover")] for c in covers]
heads_per_seat = {s: sum(h.startswith(s + "_fastener_") for h in heads) for s in seat_ids}
for s, n in heads_per_seat.items():
    if n != 2:
        rep.fail(f"{s}: {n} heads")
st.stage("unchanged_leaves")

unchanged_bad, precise_used = [], {}
for label, a in ref.items():
    if label in FINS:
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
fin1_same = not any(l == "booster_fin_fairing_1" for l, _ in unchanged_bad)
st.stage("new_parts_valid")

new_valid = {}
for label in sorted(new):
    p = parts[label]
    closed, clean = closed_and_clean(p)
    new_valid[label] = {"valid": p.is_valid, "solids": len(p.solids()), "closed": closed,
                        "check": clean, "volume_mm3": precise_volume(p), "faces": len(p.faces())}
    if not (p.is_valid and len(p.solids()) == 1 and closed and clean and p.volume > 1e-6):
        rep.fail(f"{label}: invalid {new_valid[label]}")

fin_rows, probes, head_to_lip, clear, per_seat = {}, {}, {}, {}, {}
for fin, (n, clock) in FINS.items():
    st.stage(f"fin{n}_host_volumes")
    fmeta = meta["fins"][fin]
    tan = frame(clock)[1]
    f_ref, f_new = ref[fin], parts[fin]
    removed, gained = removed_volume(f_ref, f_new)
    lost_shape = f_ref - f_new
    lost = lost_shape.solids() if lost_shape else []
    for s in lost:
        bb = s.bounding_box()
        if bb.min.X < SEAT_X[0] or bb.max.X > SEAT_X[1]:
            rep.fail(f"{fin}: removed material outside the seat window X {bb.min.X:.1f}..{bb.max.X:.1f}")
    if removed <= 1e-3:
        rep.fail(f"{fin} removed volume {removed:.6f} mm3 is not > 0")
    if gained > 1e-6:
        rep.fail(f"{fin} gained {gained:.6f} mm3")
    if abs(removed - fmeta["host_volume_removed_mm3"]) > max(5e-3, 1e-4 * removed):
        rep.fail(f"{fin}: removed {removed:.4f} != metadata {fmeta['host_volume_removed_mm3']:.4f}")
    fin_seats = [s for s in seat_ids if s.startswith(f"booster_r24_F11_{n}")]
    if len(fin_seats) != 2:
        rep.fail(f"{fin}: {len(fin_seats)} seats")

    def side_of(shape, sid):
        c = shape.center()
        return (c - bd.Vector(c.X, 0, 0)).dot(tan * fmeta["seats"][sid]["tangent_sign"]) > 0

    for sid in fin_seats:
        mine = [s for s in lost if side_of(s, sid)]
        per_seat[sid] = {"removed_mm3": sum(precise_volume(s) for s in mine), "solids": len(mine)}
        if per_seat[sid]["removed_mm3"] <= 1e-3:
            rep.fail(f"{sid}: removed no host material")
    fin_rows[fin] = {"removed_mm3": removed, "gained_mm3": gained, "removed_solids": len(lost),
                     "faces": [len(f_ref.faces()), len(f_new.faces())]}
    st.stage(f"fin{n}_crop_validity")

    box = box_around(SEAT_X[0] - 2.0, SEAT_X[1] + 2.0)
    crop_new, crop_ref = crop_shape(f_new, box), crop_shape(f_ref, box)
    c_closed, c_clean = closed_and_clean(crop_new)
    fin_rows[fin]["crop"] = {"valid": crop_new.is_valid, "closed": c_closed, "check": c_clean,
                             "faces": [len(crop_ref.faces()), len(crop_new.faces())]}
    if not (crop_new.is_valid and c_closed and c_clean):
        rep.fail(f"{fin} crop invalid: valid={crop_new.is_valid} closed={c_closed} check={c_clean}")
    st.stage(f"fin{n}_probes")

    skin_faces = []
    for sid in fin_seats:
        m = fmeta["seats"][sid]
        cover = parts[f"{sid}_cover"]
        rows, faces = {}, {}
        for pr in m["probes"]:
            name = pr["name"]
            p0, nv = bd.Vector(*pr["point_mm"]), bd.Vector(*pr["normal"]).normalized()
            faces[name] = _ray_hits(crop_ref, p0 + nv * 20.0, -nv)[0][2]
            skin = ray_skin(crop_ref, p0, nv)
            r = {"open_0.3": not crop_new.is_inside(skin - nv * 0.3),
                 "floor_0.75": crop_new.is_inside(skin - nv * 0.75),
                 "no_host_0.5": not crop_new.is_inside(skin - nv * 0.5),
                 "cover_0.4": cover.is_inside(skin - nv * 0.4),
                 "clear_0.1": not cover.is_inside(skin - nv * 0.1) and not crop_new.is_inside(skin - nv * 0.1)}
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
            if crop_new.is_inside(head.center()):
                rep.fail(f"{h}: centre inside host")
            for other in (crop_new, cover):
                inter = head & other
                if inter and inter.volume > TOL:
                    rep.fail(f"{h}: overlaps by {inter.volume:.5f} mm3")
        inter = cover & crop_new
        if inter and inter.volume > TOL:
            rep.fail(f"{sid}_cover overlaps host by {inter.volume:.5f} mm3")
    st.stage(f"fin{n}_clearance")

    fin_other = [f for f in crop_ref.faces() if not any(f.is_same(g) for g in skin_faces)]
    for sid in fin_seats:
        pieces = [s for s in lost if side_of(s, sid)]
        pieces += [parts[f"{sid}_cover"]] + [parts[h] for h in heads if h.startswith(sid)]
        bbs = [p.bounding_box() for p in pieces]
        lo = [min(getattr(b.min, a) for b in bbs) - MARGIN for a in "XYZ"]
        hi = [max(getattr(b.max, a) for b in bbs) + MARGIN for a in "XYZ"]
        grown = bd.Box(*(h - l for l, h in zip(lo, hi))).translate(
            tuple((l + h) / 2.0 for l, h in zip(lo, hi)))
        near = []
        for l, p in parts.items():
            if l == fin or l.startswith(sid + "_"):
                continue
            if not boxes_near(grown, p, 0.0):
                continue
            c = p & grown
            if c is not None and c.solids():
                near.append(c)
        d_other = min_distance(pieces, near)
        clear[sid] = {"fin_crease_ledge_blade_mm": min_distance(pieces, fin_other),
                      "other_leaves_incl_body_and_other_seat_mm":
                          d_other if d_other < MARGIN else f">= {MARGIN}",
                      "other_leaves_clipped": len(near)}
        for k in ("fin_crease_ledge_blade_mm", "other_leaves_incl_body_and_other_seat_mm"):
            v = clear[sid][k]
            if isinstance(v, float) and v < CLEARANCE - 1e-6:
                rep.fail(f"{sid}: {k} = {v:.3f} < {CLEARANCE}")
st.stage("groups_materials")

groups = {c.label: {g.label for g in c.children} for c in scene24.roots[0].children}
if not set(heads) <= groups.get(HW_GROUP, set()):
    rep.fail("heads not in the metal hardware group")
if set(covers) != groups.get(COVER_GROUP, set()):
    rep.fail("covers are not exactly the cover group")
side = json.loads(R24.with_suffix(".step.json").read_text(encoding="utf-8"))
if side.get("documentHash") != scene24.document_hash:
    rep.fail("sidecar hash does not match the saved STEP")
ap = side["appearance"]
occ = {r.label: r.ref.split("#")[-1] for r in rows24}
mat = lambda l: ap["materials"].get(ap["assignments"].get(occ[l], ""), {}).get("name")
for l in covers + heads:
    want = "Service cover paint" if l in covers else "Small metallic hardware"
    if mat(l) != want:
        rep.fail(f"{l}: material {mat(l)} != {want}")
timings = st.done()

report = {"status": "PASS" if not rep.failures else "FAIL", "failures": rep.failures,
          "document_hash": scene24.document_hash, "reference_r24p_hash": scene_p.document_hash,
          "leaves": len(parts), "r24p_leaves": len(ref), "new_leaves": sorted(new),
          "covers": covers, "heads": len(heads), "heads_per_seat": heads_per_seat,
          "fin1_unchanged_vs_r24p": fin1_same, "unchanged_failures": unchanged_bad,
          "precise_volume_rechecks_mm3": precise_used, "new_parts": new_valid,
          "fins": fin_rows, "per_seat": per_seat, "probes": probes,
          "head_centre_to_lip_mm": head_to_lip, "clearance_mm": clear, "stage_seconds": timings}
OUT.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("status", "failures", "fin1_unchanged_vs_r24p", "fins",
                                         "per_seat", "head_centre_to_lip_mm", "clearance_mm",
                                         "precise_volume_rechecks_mm3", "stage_seconds")},
                 indent=1, default=float))
sys.exit(rep.exit_code())
