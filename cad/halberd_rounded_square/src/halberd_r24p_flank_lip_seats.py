"""R24p F11 one-fin prototype: R20-style folded seats over the fairing lip of
booster_fin_fairing_1 (clock 45), per side one seat running from the ledge beside the
blade root, over the sharp lip (crease, r ~137.5) and down onto the fairing flank.

Cosmetic game-asset detailing only, built on the saved R20 model (read-only).

Measured (R23p sections + this pass): beside the blade root a flat ledge (normal ~ the
fin clock) runs out to the lip; its width grows forward as the blade thins (about 1.6 mm
at X -1290, 2.4 at -1270, 3.3 at -1250, 4.2 at -1230). Below the lip the flank turns
~76 deg away and is ~26 mm tall. As in R20 (root -> narrow land -> crease -> spacious
facet), the ledge is the narrow land and the flank is the spacious facet, so both heads
sit on the flank, 2.4 mm past the lip. With the R20 root gap of 2.25 mm the ledge strip
at the accepted X -1262 would shrink to ~0-1 mm at the aft end, so the seat is moved
forward to X -1232 (span -1244..-1220, still on the clean flank run that ends at the
fairing nose, X -1204), where the strip is about 1-2.3 mm.

Construction (R20 F07 method, R23p rays): ledge points from radial rays at the fin clock,
flank points from rays along the flank's own normal ("flank clock"); the root edge and
the lip are bisected on face identity; seat points are analytic (planar ledge, planar
flank per section) and snapped to the native skin. Outline vertices are added where the
tapered side edges cross the lip. The frame normal bisects ledge and flank normals; the
outline prism clips both native faces and each patch is extruded along its own normal,
so pocket and cover fold over the lip.
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

from cadgen import build123d as bd, read_scene, srgb, step

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
import surface_detail  # noqa: E402
from surface_detail import (_ray_hits, backing_depth, checked_cut, clock_frame,  # noqa: E402
                            seated_hardware)
from root_geometry import bisect, chamfered, local_crop_box  # noqa: E402
from check_kit import Stages, min_distance, precise_volume  # noqa: E402

from halberd_r17_interface_shapes import FASTENER_SEAT_DEPTH, _slotted_head_local  # noqa: E402
from halberd_r18_access_shapes import BODY_PAINT, FASTENER_REMAINING_WALL_MIN, METAL  # noqa: E402
import halberd_r19_surface_proto as proto  # noqa: E402
import halberd_r20_fin_seats as r20  # noqa: E402
from halberd_r22p_booster_seats import _layer, _skin_patches  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / "STEP" / "halberd_r20_fin_seats.step"
OUTPUT_METADATA = ROOT / "reviews" / "halberd_r24p_flank_lip_seats.json"
FIN, CLOCK = "booster_fin_fairing_1", 45.0
SIDES = (("p", +1), ("m", -1))
HARDWARE_GROUP = r20.HARDWARE_GROUP
COVER_GROUP = "r24p_lip_seat_covers"

SEAT_X = -1232.0
PROBE_R = 128.0            # radius of the first flank hit (mid-flank)
ROOT_GAP = 2.25            # arc from the blade root edge to the long edge (on the ledge)
SEAT_WIDTH = 9.5           # R20: across the skin, folding over the lip
INNER_HALF = 12.0          # 24 mm root-side edge (R22p/R23p length)
OUTER_HALF = 8.0           # 16 mm lower edge on the flank
CORNER = 0.8
POCKET_DEPTH = 0.60
COVER_SETBACK = 0.18
PERIMETER_GAP = 0.30
OVERRUN = 0.20
SCREW_U = (-6.0, 6.0)
HEAD_PAST_CREASE = 2.4     # R20: head centre arc distance beyond the lip (on the flank)
HEAD_EDGE_MARGIN = 2.9     # R20: head centre to the outer pocket edge, minimum
MIN_STRIP = 0.8            # ledge strip (root-side edge to lip), minimum
SNAP_TOL = 0.02
FEATURE_CLEARANCE = 2.0
CROP_X, CROP_T, CROP_R = (-1270.0, -1200.0), (-40.0, 40.0), (100.0, 180.0)

CALLS = {"skin_point": 0}


def _skin(host, x, t, clock):
    CALLS["skin_point"] += 1
    return surface_detail.skin_point(host, x, t, clock)


class Lip:
    """Ledge (land) + lip (crease) + flank (facet) beside one side of the blade."""

    def __init__(self, crop, side):
        self.crop, self.side = crop, side
        self.rad, tan = clock_frame(CLOCK)
        self.tan = tan * side
        self.axis = bd.Vector(1.0, 0.0, 0.0)
        hits = _ray_hits(crop, bd.Vector(SEAT_X, 0.0, 0.0) + self.rad * PROBE_R + self.tan * 40.0,
                         -self.tan)
        if not hits:
            raise ValueError(("flank probe missed", side))
        _, p, self.flank = hits[0]
        n = self.flank.normal_at(p).normalized()
        n = n if n.dot(self.tan) > 0.0 else -n
        self.fclock = math.degrees(math.atan2(n.Y, n.Z))
        _, self.ftan = clock_frame(self.fclock)
        self.ft_ref = p.dot(self.ftan)
        self.ledge, self.t_ledge = None, None
        for k in range(2, 30):                       # first ledge hit outward from the blade
            t = 0.25 * k
            try:
                h = _skin(crop, SEAT_X, side * t, CLOCK)
            except ValueError:
                continue
            if h["normal"].dot(self.rad) > 0.9 and 134.0 < h["measured_radius_mm"] < 141.0:
                self.ledge = h["face"]
                break
        if self.ledge is None:
            raise ValueError(("ledge not found", side))
        self.t_ledge = t + 0.3
        e0 = self._edge(SEAT_X, self.t_ledge)
        c0 = self._crease(SEAT_X)
        self.t_ledge = (e0 + c0) / 2.0
        self._cache = {}
        ends = (SEAT_X - INNER_HALF - 1.0, SEAT_X + INNER_HALF + 1.0)
        self.e_ends = {x: self._edge(x, self.t_ledge) for x in ends}
        self.c_ends = {x: self._crease(x) for x in ends}
        for name, ends_map, mid in (("root edge", self.e_ends, e0), ("lip", self.c_ends, c0)):
            if abs(mid - self._lin(ends_map, SEAT_X)) > 0.03:
                raise ValueError((name + " is not straight", side, mid, self._lin(ends_map, SEAT_X)))

    def on_ledge(self, x, t):
        try:
            return _skin(self.crop, x, self.side * t, CLOCK)["face"].is_same(self.ledge)
        except ValueError:
            return False

    def _edge(self, x, t_in):
        if self.on_ledge(x, 0.0) or not self.on_ledge(x, t_in):
            raise ValueError(("root edge not bracketed", x, self.side))
        return bisect(lambda t: self.on_ledge(x, t), 0.0, t_in)

    def _crease(self, x):
        t_in = self.t_ledge
        if not self.on_ledge(x, t_in) or self.on_ledge(x, t_in + 8.0):
            raise ValueError(("lip not bracketed", x, self.side))
        return bisect(lambda t: not self.on_ledge(x, t), t_in, t_in + 8.0)

    @staticmethod
    def _lin(ends_map, x):
        (x0, a), (x1, b) = sorted(ends_map.items())
        return a + (b - a) * (x - x0) / (x1 - x0)

    def section(self, x):
        """(root point, lip point, ledge chord wc, flank normal) at X = x."""
        key = round(x, 6)
        if key not in self._cache:
            e, c = self._lin(self.e_ends, x), self._lin(self.c_ends, x)
            root = _skin(self.crop, x, self.side * (e + 1e-3), CLOCK)["point"]
            lip = _skin(self.crop, x, self.side * (c - 1e-3), CLOCK)["point"]
            hf = _skin(self.crop, x, self.ft_ref, self.fclock)
            if not hf["face"].is_same(self.flank):
                raise ValueError(("flank face changed", x, self.side))
            self._cache[key] = (root, lip, (lip - root).length, hf["normal"])
        return self._cache[key]

    def wc(self, x):
        return self.section(x)[2]

    def point(self, u, w, snap=True):
        """Skin point at X = SEAT_X + u, arc w from the root edge (ledge, then flank)."""
        x = SEAT_X + u
        root, lip, wc, nf = self.section(x)
        if w <= wc:
            p = root + (lip - root).normalized() * w
            if not snap:
                return p
            h = _skin(self.crop, x, self.side * (p - bd.Vector(x, 0, 0)).dot(self.tan), CLOCK)
            face = self.ledge
        else:
            d = self.axis.cross(nf).normalized()
            d = d if d.dot(self.rad) < 0.0 else -d
            p = lip + d * (w - wc)
            if not snap:
                return p
            h = _skin(self.crop, x, p.dot(self.ftan), self.fclock)
            face = self.flank
        if not h["face"].is_same(face) or (h["point"] - p).length > SNAP_TOL:
            raise ValueError(("seat point off the skin", u, w, self.side, (h["point"] - p).length))
        return h["point"]


def outline_uw(lip):
    """Tapered chamfered outline; extra vertices where edges cross the lip (w = wc(u))."""
    g, h = ROOT_GAP, ROOT_GAP + SEAT_WIDTH
    base = chamfered([(-INNER_HALF, g), (INNER_HALF, g), (OUTER_HALF, h), (-OUTER_HALF, h)],
                     CORNER)
    (x0, w0), (x1, w1) = [(x, lip.wc(x)) for x in (SEAT_X - INNER_HALF, SEAT_X + INNER_HALF)]
    wc_u = lambda u: w0 + (w1 - w0) * (SEAT_X + u - x0) / (x1 - x0)
    out = []
    for i, a in enumerate(base):
        b = base[(i + 1) % len(base)]
        out.append((a, "pt"))
        fa, fb = a[1] - wc_u(a[0]), b[1] - wc_u(b[0])
        if fa * fb < 0.0:
            s = fa / (fa - fb)
            out.append(((a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s), "lip"))
    return out


def build_seat(crop, side_key, side):
    tag = f"booster_r24p_F11_1{side_key}"
    lip = Lip(crop, side)
    strips = {u: lip.wc(SEAT_X + u) - ROOT_GAP for u in (-INNER_HALF, INNER_HALF)}
    if min(strips.values()) < MIN_STRIP:
        raise ValueError((tag, "ledge strip too narrow", strips))
    root0, lip0, wc0, nf0 = lip.section(SEAT_X)
    n_ledge = _skin(crop, SEAT_X, side * lip.t_ledge, CLOCK)["normal"]
    normal = (n_ledge + nf0).normalized()
    origin = lip0
    x_dir = (lip.axis - normal * normal.dot(lip.axis)).normalized()
    y_dir = normal.cross(x_dir)
    plane = bd.Plane(origin=origin, x_dir=x_dir, z_dir=normal)

    world, local = [], []
    for (u, w), kind in outline_uw(lip):
        p = lip.point(u, lip.wc(SEAT_X + u), snap=False) if kind == "lip" else lip.point(u, w)
        world.append(p)
        local.append(((p - origin).dot(x_dir), (p - origin).dot(y_dir)))
    outline = bd.Wire.make_polygon([(a, b, 0.0) for a, b in local], close=True)
    faces = [lip.ledge, lip.flank]
    found, pocket_area = _skin_patches(faces, outline, plane, normal, f"{tag}_pocket")
    pocket = _layer(found, OVERRUN, POCKET_DEPTH, None, f"{tag}_pocket")
    pocket.label = f"{tag}_pocket"
    cover_found, cover_area = _skin_patches(faces, outline.offset_2d(-PERIMETER_GAP), plane,
                                            normal, f"{tag}_cover")
    cover = _layer(cover_found, -COVER_SETBACK, POCKET_DEPTH, crop, f"{tag}_cover")
    fold_wall = backing_depth(crop, lip0, normal)

    screws, screw_w = [], []
    for u in SCREW_U:
        w = lip.wc(SEAT_X + u) + HEAD_PAST_CREASE
        if ROOT_GAP + SEAT_WIDTH - w < HEAD_EDGE_MARGIN:
            raise ValueError((tag, "head too close to the outer seat edge", u, w))
        p = lip.point(u, w)
        screws.append((u, p.dot(lip.ftan)))
        screw_w.append(w)
    head_local, _ = _slotted_head_local()
    CALLS["skin_point"] += len(screws)          # one skin_point per site inside seated_hardware
    seats, heads, sites = seated_hardware(
        crop, SEAT_X, lip.fclock, screws, proto.seat_tool_extended(), head_local,
        seat_depth=FASTENER_SEAT_DEPTH, min_remaining_wall=FASTENER_REMAINING_WALL_MIN,
        label_prefix=tag, color=srgb(METAL))
    for seat in seats:
        cover = checked_cut(cover, seat)
    if not cover.is_valid or len(cover.solids()) != 1:
        raise ValueError((tag, "cover invalid after seat cuts"))
    cover = cover.solids()[0]
    cover.label, cover.color = f"{tag}_cover", srgb(BODY_PAINT)

    # Probe sites for the checker: ledge strip (widest end), flank near the heads, flank low.
    probes = []
    for name, u, w, n in (("ledge_fwd", 8.0, None, n_ledge), ("flank_mid", 0.0, wc0 + 2.4, nf0),
                          ("flank_low", 0.0, ROOT_GAP + SEAT_WIDTH - 1.6, nf0),
                          ("flank_low_aft", -3.0, ROOT_GAP + SEAT_WIDTH - 1.6, nf0)):
        if w is None:
            w = (ROOT_GAP + lip.wc(SEAT_X + u)) / 2.0
        probes.append({"name": name, "point_mm": list(lip.point(u, w)), "normal": list(n)})
    return {
        "pocket": pocket, "seats": list(seats), "cover": cover, "heads": list(heads),
        "skin_faces": faces,
        "meta": {
            "fin": FIN, "fin_clock_degrees": CLOCK, "flank_clock_degrees": lip.fclock,
            "side": side_key, "tangent_sign": side, "center_x_mm": SEAT_X,
            "frame_origin_mm": list(origin), "frame_normal": list(normal),
            "ledge_normal": list(n_ledge), "flank_normal": list(nf0),
            "lip_turn_deg": math.degrees(math.acos(max(-1.0, min(1.0, n_ledge.dot(nf0))))),
            "ledge_chord_root_to_lip_mm": {f"{SEAT_X + u:g}": lip.wc(SEAT_X + u)
                                           for u in (-INNER_HALF, 0.0, INNER_HALF)},
            "ledge_strip_mm": {f"{SEAT_X + u:g}": v for u, v in strips.items()},
            "root_gap_mm": ROOT_GAP, "width_mm": SEAT_WIDTH,
            "inner_length_mm": 2 * INNER_HALF, "outer_length_mm": 2 * OUTER_HALF,
            "corner_chamfer_mm": CORNER, "pocket_depth_mm": POCKET_DEPTH,
            "cover_setback_mm": COVER_SETBACK, "perimeter_gap_mm": PERIMETER_GAP,
            "outline_world_mm": [list(p) for p in world],
            "pocket_patch_area_mm2": pocket_area, "cover_patch_area_mm2": cover_area,
            "wall_behind_fold_along_frame_normal_mm": fold_wall,
            "screw_arc_from_root_mm": screw_w, "head_past_lip_mm": HEAD_PAST_CREASE,
            "screw_sites": list(sites), "probes": probes,
            "cover_label": cover.label, "head_labels": [h.label for h in heads],
        },
    }


def build_r24p():
    st = Stages(stage_budget_s=200.0, total_budget_s=290.0)
    scene = read_scene(SAVED)
    saved = {r.label: scene.resolve(r.ref).shape() for r in scene.leaves()}
    fin0 = saved[FIN]
    st.stage("crop")
    fc = fin0 & local_crop_box(CLOCK, CROP_X, CROP_T, CROP_R)
    st.stage("seats")

    built = [build_seat(fc, key, s) for key, s in SIDES]
    st.stage("clearance")
    new_parts = [p for b in built for p in (b["pocket"], b["cover"], *b["heads"])]
    skin = [f for b in built for f in b["skin_faces"]]
    fin_other = [f for f in fc.faces() if not any(f.is_same(g) for g in skin)]
    gap_fin = min_distance(new_parts, fin_other)
    obstacles = [p for l, p in saved.items() if l != FIN]
    gap_detail = min_distance(new_parts, obstacles)
    gap_seats = min_distance([built[0]["pocket"]], [built[1]["pocket"]])
    if min(gap_fin, gap_detail, gap_seats) < FEATURE_CLEARANCE:
        raise ValueError(("seat within clearance", gap_fin, gap_detail, gap_seats))
    st.stage("cut_fin")

    fin1, removed = fin0, {}
    for cutter in [c for b in built for c in (b["pocket"], *b["seats"])]:
        before = precise_volume(fin1)
        fin1 = checked_cut(fin1, cutter)
        removed[cutter.label] = before - precise_volume(fin1)
        if removed[cutter.label] <= 1e-3:
            raise ValueError((cutter.label, "cutter removed no host material"))
    if not fin1.is_valid or len(fin1.solids()) != 1:
        raise ValueError("fin leaf invalid or split after seat cuts")
    fin1 = fin1.solids()[0]
    for b in built:
        for head in b["heads"]:
            if fin1.is_inside(head.center()):
                raise ValueError((head.label, "head centre inside host"))
    st.stage("assemble")

    fin1.label, fin1.color = FIN, fin0.color
    heads = [h for b in built for h in b["heads"]]
    covers = [b["cover"] for b in built]
    labels = [p.label for p in heads + covers]
    if len(set(labels)) != len(labels) or set(labels) & set(saved):
        raise ValueError("duplicate R24p labels")
    children = []
    for node in scene.roots[0].children:
        if node.label == HARDWARE_GROUP:
            group = r20._rebuild(scene, node, {})
            children.append(bd.Compound(children=[*group.children, *heads], label=HARDWARE_GROUP))
        else:
            children.append(r20._rebuild(scene, node, {FIN: fin1}))
    children.append(bd.Compound(children=covers, label=COVER_GROUP))

    meta = {
        "source_step": str(SAVED.relative_to(ROOT)), "source_document_hash": scene.document_hash,
        "units": "mm; clock 0 = +Z, 90 = +Y; tangent = (0, cos, -sin)",
        "seats": {b["meta"]["cover_label"][:-len("_cover")]: b["meta"] for b in built},
        "host": FIN, "removed_mm3": removed, "host_volume_removed_mm3": sum(removed.values()),
        "faces": {"fin_before": len(fin0.faces()), "fin_after": len(fin1.faces()),
                  "cover_faces": [len(c.faces()) for c in covers],
                  "head_faces": [len(h.faces()) for h in heads]},
        "skin_point_calls": CALLS["skin_point"],
        "min_distance_to_other_fin_faces_mm": gap_fin,
        "min_distance_to_other_leaves_mm": gap_detail,
        "min_distance_between_seats_mm": gap_seats,
        "hardware_group": HARDWARE_GROUP, "cover_group": COVER_GROUP,
        "hardware_labels": [h.label for h in heads], "cover_labels": [c.label for c in covers],
    }
    meta["stage_seconds"] = st.done()
    OUTPUT_METADATA.write_text(json.dumps(meta, indent=2, default=float) + "\n", encoding="utf-8")
    return bd.Compound(children=children, label="halberd_r24p_flank_lip_seats")


def _materials():
    materials = copy.deepcopy(r20.MATERIALS)
    materials["assignments"].append({"targets": [f"#{COVER_GROUP}"], "material": "detail_paint"})
    return materials


MATERIALS = _materials()


@step(out="../STEP/r24p_flank_seats.step", materials=MATERIALS)
def r24p_flank_seats():
    return build_r24p()


if __name__ == "__main__":
    r24p_flank_seats()
