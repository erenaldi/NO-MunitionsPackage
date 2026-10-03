"""R20 F07: main-fin root attachment seats on the saved R19 surface model.

Cosmetic game-asset detailing only. One shaped seat on each side of each of
the four main-fin roots (8 seats): a 0.6 mm conformal pocket cut from the
native host skin (F02 / R18 method: native skin patches clipped by a local
outline prism, extruded inward and intersected with the host), a cover plate
set 0.18 mm below the skin with a 0.3 mm perimeter gap, and two R17 slotted
heads per seat (16) placed from measured skin points and normals.

Measured skin beside each root (2026-10-02, this pass): not a smooth curve but
a flat diagonal land (normal along the fin clock) that ends at a sharp crease
5.9-6.7 mm from the visible root edge, beyond which the next facet is turned
~65 deg. A 2.25 mm root gap leaves only ~4 mm of land, too little for an R17
countersink (dia ~3.6 mm) with cover margin, so each seat wraps conformally
over the crease and its two heads sit on the outer facet, 2.4 mm past the
crease. The seat is therefore ~9.5 mm across instead of 8 mm.

Seat outline, in (u, w): u = body X from the seat centre, w = arc length on
the skin (in the X = const section) from the measured visible root edge. The
root-side edge is w = ROOT_GAP at every 1 mm station, i.e. an offset of the
measured root outline; the ends taper from the 20 mm root edge to a 13 mm
outer edge; all corners carry a 0.8 mm chamfer. (u, w) maps to 3D through the
measured land and facet: root edge bisected per station where the host skin
leaves the fin solid, crease bisected where the skin normal turns.

Reads the saved R19 STEP from the main checkout (read-only): in this worktree
the R19 STEP bytes differ from its sidecar hash because of line-ending
conversion. All R19 leaves are carried over unchanged except the main host,
which only loses the declared pocket and seat volumes. New heads join the R19
metal hardware group; new covers form their own paint group.
"""
from __future__ import annotations

import copy
import json
import math
import os
import sys
from pathlib import Path

from cadgen import build123d as bd, read_scene, srgb, step
try:
    from cadgen import declare_input
except ImportError:  # cadgen >= 0.7.10 traces input reads itself
    def declare_input(_path):
        return None

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from surface_detail import checked_cut, clock_frame, seated_hardware, skin_point  # noqa: E402

from halberd_r17_interface_shapes import FASTENER_SEAT_DEPTH, _slotted_head_local  # noqa: E402
from halberd_r18_access_shapes import (BODY_PAINT, FASTENER_REMAINING_WALL_MIN,  # noqa: E402
                                       METAL)
import halberd_r19_surface as r19  # noqa: E402
import halberd_r19_surface_proto as proto  # noqa: E402
from halberd_r19_intake_walls import precise_volume  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SAVED = Path(os.environ.get(
    "R19_SAVED_STEP",
    r"C:\Users\erena\Desktop\Nuclear Option Munitions Package\cad\halberd_rounded_square\STEP\halberd_r19_surface.step"))
OUTPUT_METADATA = ROOT / "reviews" / "halberd_r20_fin_seats.json"
MAIN_HOST = "main_body_intake_r12"
HARDWARE_GROUP = r19.HARDWARE_GROUP          # "r19_surface_hardware" (metal)
COVER_GROUP = "r20_fin_seat_covers"
FINS = (("main_fin_1", 45.0), ("main_fin_2", 135.0), ("main_fin_3", 225.0),
        ("main_fin_4", 315.0))
SIDES = (("p", +1), ("m", -1))               # +tangent / -tangent side of the blade

SEAT_X = -970.0           # seat centre (root chord -1075..-859.8, thickest ~-975)
ROOT_GAP = 2.25           # arc from visible root edge to the pocket's root-side edge
SEAT_WIDTH = 9.5          # across the skin (wraps over the land/facet crease)
INNER_HALF = 10.0         # root-side edge half length (20 mm)
OUTER_HALF = 6.5          # outer edge half length (13 mm): tapered ends
CORNER = 0.8              # corner chamfer
POCKET_DEPTH = 0.60
COVER_SETBACK = 0.18
PERIMETER_GAP = 0.30
SCREW_U = (-4.5, 4.5)     # two heads per seat
HEAD_PAST_CREASE = 2.4    # head centre arc distance beyond the crease (on the facet)
HEAD_EDGE_MARGIN = 2.9    # head centre to outer pocket edge, minimum
FEATURE_CLEARANCE = 2.0
CROP_X = (-995.0, -945.0)  # local measurement crop (exact host faces)


def _bisect(pred, lo, hi, iterations=22):
    """pred(lo) False, pred(hi) True -> boundary."""
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        if pred(mid):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


class RootSide:
    """Measured skin beside one fin side: root edge, land, crease, facet."""

    def __init__(self, crop, fin, clock, side):
        self.crop, self.fin, self.clock, self.side = crop, fin, clock, side
        self.radial, self.tangent = clock_frame(clock)
        self.axis = bd.Vector(1.0, 0.0, 0.0)
        self._edge = {}
        # Crease: absolute |tangent offset| at the two ends (checked mid-way).
        self.crease_ends = {x: self._crease_abs(x) for x in (SEAT_X - INNER_HALF,
                                                           SEAT_X + INNER_HALF)}
        mid = self._crease_abs(SEAT_X)
        if abs(mid - self.crease_t(SEAT_X)) > 0.02:
            raise ValueError(("crease line is not straight", clock, side, mid,
                              self.crease_t(SEAT_X)))

    def hit(self, x, t_abs):
        return skin_point(self.crop, x, self.side * t_abs, self.clock)

    def edge(self, x):
        key = round(x, 6)
        if key not in self._edge:
            def outside(t):
                h = self.hit(x, t)
                return not self.fin.is_inside(h["point"] + h["normal"] * 0.05)
            if outside(0.0) or not outside(8.0):
                raise ValueError(("root edge not bracketed", x, self.clock, self.side))
            self._edge[key] = _bisect(outside, 0.0, 8.0)
        return self._edge[key]

    def _crease_abs(self, x):
        e = self.edge(x)
        n0 = self.hit(x, e + 0.5)["normal"]
        turned = lambda t: self.hit(x, t)["normal"].dot(n0) < 0.99
        if turned(e + 1.0) or not turned(e + 12.0):
            raise ValueError(("crease not bracketed", x, self.clock, self.side))
        return _bisect(turned, e + 1.0, e + 12.0)

    def crease_t(self, x):
        (x0, c0), (x1, c1) = sorted(self.crease_ends.items())
        return c0 + (c1 - c0) * (x - x0) / (x1 - x0)

    def crease_w(self, x):
        return self.crease_t(x) - self.edge(x)

    def _dir(self, normal):
        d = self.axis.cross(normal).normalized()
        return d if d.dot(self.tangent * self.side) > 0.0 else -d

    def point(self, u, w):
        """3D skin point at (u, w); land is planar, facet planar per section."""
        x = SEAT_X + u
        e, tc = self.edge(x), self.crease_t(x)
        land = self.hit(x, (e + tc) / 2.0)
        n0 = land["normal"]
        root = self.hit(x, e)["point"]
        wc = tc - e
        if w <= wc:
            return root + self._dir(n0) * w
        crease = root + self._dir(n0) * wc
        n1 = self.hit(x, tc + 1.5)["normal"]
        return crease + self._dir(n1) * (w - wc)


def _chamfered(points, size):
    out = []
    n = len(points)
    for i, p in enumerate(points):
        for q in (points[i - 1], points[(i + 1) % n]):   # towards previous, then next
            d = math.hypot(q[0] - p[0], q[1] - p[1])
            out.append((p[0] + (q[0] - p[0]) * size / d, p[1] + (q[1] - p[1]) * size / d))
    return out


def _densify(points, spacing=1.0):
    dense = []
    n = len(points)
    for i, a in enumerate(points):
        b = points[(i + 1) % n]
        steps = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / spacing)))
        for k in range(steps):
            f = k / steps
            dense.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return dense


def seat_outline_uw():
    """Closed (u, w) outline: tapered, chamfered, root edge at w = ROOT_GAP."""
    g, h = ROOT_GAP, ROOT_GAP + SEAT_WIDTH
    base = [(-INNER_HALF, g), (INNER_HALF, g), (OUTER_HALF, h), (-OUTER_HALF, h)]
    return _densify(_chamfered(base, CORNER))


def _union(shapes):
    result = shapes[0]
    for s in shapes[1:]:
        result = result + s
    return result


def build_seat(host, crop, fin, visible_fin, fin_label, clock, side_key, side, obstacles):
    tag = f"main_r20_F07_{fin_label.split('_')[-1]}{side_key}"
    rs = RootSide(crop, fin, clock, side)

    # Local frame: origin on the crease at the seat centre, normal bisecting
    # the land and facet normals so the outline projects without folding.
    wc0 = rs.crease_w(SEAT_X)
    origin = rs.point(0.0, wc0)
    n_land = rs.hit(SEAT_X, rs.edge(SEAT_X) + wc0 / 2.0)["normal"]
    n_facet = rs.hit(SEAT_X, rs.crease_t(SEAT_X) + 1.5)["normal"]
    normal = (n_land + n_facet).normalized()
    x_dir = (rs.axis - normal * normal.dot(rs.axis)).normalized()
    y_dir = normal.cross(x_dir)
    plane = bd.Plane(origin=origin, x_dir=x_dir, z_dir=normal)

    faces, world, local, worst = [], [], [], 1.0
    for u, w in seat_outline_uw():
        p = rs.point(u, w)
        t = (p - bd.Vector(p.X, 0.0, 0.0)).dot(rs.tangent)
        h = skin_point(crop, p.X, t, clock)
        if (h["point"] - p).length > 0.02:
            raise ValueError((tag, "analytic seat point is off the skin", u, w,
                              (h["point"] - p).length))
        worst = min(worst, h["normal"].dot(normal))
        if not any(h["face"].is_same(f) for f in faces):
            faces.append(h["face"])
        world.append(p)
        local.append(((p - origin).dot(x_dir), (p - origin).dot(y_dir)))
    if worst < 0.5:
        raise ValueError((tag, "skin turns too far from the seat frame", worst))

    outline = bd.Wire.make_polygon([(a, b, 0.0) for a, b in local], close=True)

    def patches(face):
        m = bd.Solid.extrude(face.moved(bd.Location((0.0, 0.0, -40.0))),
                             bd.Vector(0.0, 0.0, 80.0)).moved(plane.location)
        found = []
        for f in faces:
            clipped = f & m
            for patch in (clipped.faces() if clipped else []):
                n = patch.normal_at().normalized()
                if n.dot(normal) < 0.0:
                    n = -n
                if patch.area > 1e-6 and n.dot(normal) >= 0.25:
                    found.append((patch, n))
        area = sum(p.area for p, _ in found)
        if area < face.area * 0.995:
            raise ValueError((tag, "native skin clipped the seat outline", face.area, area))
        return found, area

    def shell(found, offset, thickness, label):
        sections = []
        for patch, n in found:    # each native patch along its own normal
            start = patch.moved(bd.Location(-n * offset)) if offset else patch
            section = bd.Solid.extrude(start, -n * thickness) & crop
            if not section or section.volume <= 0.0 or not section.is_valid:
                raise ValueError((label, "skin extrusion missed the host"))
            sections.append(section)
        result = _union(sections).clean()
        if not result.is_valid or len(result.solids()) != 1:
            raise ValueError((label, "seat solid invalid or split", len(result.solids())))
        return result.solids()[0]

    pocket_patches, pocket_area = patches(bd.Face(outline))
    pocket = shell(pocket_patches, 0.0, POCKET_DEPTH, f"{tag}_pocket")
    pocket.label = f"{tag}_pocket"
    cover_patches, cover_area = patches(bd.Face(outline.offset_2d(-PERIMETER_GAP)))
    cover = shell(cover_patches, COVER_SETBACK, POCKET_DEPTH - COVER_SETBACK, f"{tag}_cover")

    # Heads from measured skin points/normals on the uncut host (outer facet).
    screws, screw_w = [], []
    for u in SCREW_U:
        w = rs.crease_w(SEAT_X + u) + HEAD_PAST_CREASE
        if ROOT_GAP + SEAT_WIDTH - w < HEAD_EDGE_MARGIN:
            raise ValueError((tag, "head too close to the outer seat edge", u, w))
        p = rs.point(u, w)
        screws.append((u, (p - bd.Vector(p.X, 0.0, 0.0)).dot(rs.tangent)))
        screw_w.append(w)
    head_local, _ = _slotted_head_local()
    seats, heads, sites = seated_hardware(
        crop, SEAT_X, clock, screws, proto.seat_tool_extended(), head_local,
        seat_depth=FASTENER_SEAT_DEPTH, min_remaining_wall=FASTENER_REMAINING_WALL_MIN,
        label_prefix=tag, color=srgb(METAL))
    for seat in seats:
        cover = checked_cut(cover, seat)
    if not cover.is_valid or len(cover.solids()) != 1:
        raise ValueError((tag, "cover invalid after seat cuts"))
    cover = cover.solids()[0]
    cover.label, cover.color = f"{tag}_cover", srgb(BODY_PAINT)

    gap_fin = min(part.distance_to(visible_fin) for part in (pocket, cover, *heads))
    if gap_fin < FEATURE_CLEARANCE:
        raise ValueError((tag, "seat within clearance of the visible fin root", gap_fin))
    for part in (pocket, cover, *heads):
        blocker = r19._near(part, obstacles, FEATURE_CLEARANCE)
        if blocker:
            raise ValueError((part.label, "within clearance of", blocker))
    return {
        "pocket": pocket, "seats": seats, "cover": cover, "heads": heads,
        "meta": {
            "fin": fin_label, "clock_degrees": clock, "side": side_key, "tangent_sign": side,
            "center_x_mm": SEAT_X, "frame_origin_mm": list(origin),
            "frame_normal": list(normal), "land_normal": list(n_land),
            "facet_normal": list(n_facet),
            "facet_turn_deg": math.degrees(math.acos(max(-1.0, min(1.0, n_land.dot(n_facet))))),
            "crease_arc_from_root_mm": {f"{SEAT_X + u:g}": rs.crease_w(SEAT_X + u)
                                        for u in (-INNER_HALF, 0.0, INNER_HALF)},
            "root_edge_tangent_mm": [[SEAT_X + u, side * rs.edge(SEAT_X + u)]
                                     for u in range(-int(INNER_HALF), int(INNER_HALF) + 1)],
            "root_gap_arc_mm": ROOT_GAP, "width_arc_mm": SEAT_WIDTH,
            "inner_length_mm": 2 * INNER_HALF, "outer_length_mm": 2 * OUTER_HALF,
            "corner_chamfer_mm": CORNER, "pocket_depth_mm": POCKET_DEPTH,
            "cover_setback_mm": COVER_SETBACK, "perimeter_gap_mm": PERIMETER_GAP,
            "outline_local_mm": [list(p) for p in local],
            "outline_world_mm": [list(p) for p in world],
            "min_outline_normal_dot_frame": worst,
            "pocket_patch_area_mm2": pocket_area, "cover_patch_area_mm2": cover_area,
            "native_faces": len(faces),
            "pocket_tool_volume_mm3": pocket.volume, "cover_volume_mm3": cover.volume,
            "min_distance_to_visible_fin_mm": gap_fin,
            "screw_arc_from_root_mm": screw_w,
            "screw_sites": list(sites),
            "cover_label": cover.label, "head_labels": [h.label for h in heads],
        },
    }


def _rebuild(scene, node, replace):
    if node.children:
        return bd.Compound(children=[_rebuild(scene, c, replace) for c in node.children],
                           label=node.label)
    return replace.get(node.label) or scene.resolve(node.ref).shape()


def build_r20_fin_seats():
    declare_input(SAVED)
    scene = read_scene(SAVED)
    rows = tuple(scene.leaves())
    saved = {r.label: scene.resolve(r.ref).shape() for r in rows}
    if len(saved) != len(rows):
        raise ValueError("duplicate leaf labels in saved R19")
    host_before = saved[MAIN_HOST]
    box = bd.Box(CROP_X[1] - CROP_X[0], 600.0, 600.0).translate(
        ((CROP_X[0] + CROP_X[1]) / 2.0, 0.0, 0.0))
    crop = host_before & box
    obstacles = [p for label, p in saved.items()
                 if label != MAIN_HOST and not label.startswith("main_fin_")
                 and not label.startswith("booster")]
    meta = {"source_step": str(SAVED), "source_document_hash": scene.document_hash,
            "units": "mm; clock 0 = +Z, 90 = +Y; tangent = (0, cos, -sin)",
            "seats": {}, "cuts": []}

    built = []
    for fin_label, clock in FINS:
        fin = saved[fin_label]
        visible = fin - host_before
        others = obstacles + [saved[l] for l, _ in FINS if l != fin_label]
        for side_key, side in SIDES:
            built.append(build_seat(host_before, crop, fin, visible, fin_label, clock,
                                    side_key, side, others))
            print("seat", built[-1]["meta"]["cover_label"], flush=True)

    for i, a in enumerate(built):
        for b in built[i + 1:]:
            d = a["pocket"].distance_to(b["pocket"])
            if d < FEATURE_CLEARANCE:
                raise ValueError(("seats too close", a["meta"]["cover_label"], d))

    # Host cuts: every cutter must remove material (OCC silent no-op guard).
    host = host_before
    for seat in built:
        seat_id = seat["meta"]["cover_label"].replace("_cover", "")
        removed = {}
        for cutter in (seat["pocket"], *seat["seats"]):
            # Default-precision volume deltas on the ~85e6 mm3 host are only
            # good to ~0.1 mm3, so record the removed solid's own volume.
            taken = host & cutter
            host = checked_cut(host, cutter)
            removed[cutter.label] = precise_volume(taken) if taken else 0.0
            if removed[cutter.label] <= 1e-3:
                raise ValueError((cutter.label, "cutter removed no host material"))
            meta["cuts"].append({"seat": seat_id, "cutter": cutter.label,
                                 "removed_mm3": removed[cutter.label]})
        if not host.is_valid or len(host.solids()) != 1:
            raise ValueError((seat_id, "host invalid or split after seat cuts"))
        for head in seat["heads"]:
            if host.is_inside(head.center()):
                raise ValueError((head.label, "head centre inside host"))
        seat["meta"]["removed_mm3"] = sum(removed.values())
        meta["seats"][seat_id] = seat["meta"]
    host = host.solids()[0]
    host.label, host.color = MAIN_HOST, host_before.color

    heads = [h for s in built for h in s["heads"]]
    covers = [s["cover"] for s in built]
    labels = [p.label for p in heads + covers]
    if len(set(labels)) != len(labels) or set(labels) & set(saved):
        raise ValueError("duplicate R20 labels")

    children = []
    for node in scene.roots[0].children:
        if node.label == HARDWARE_GROUP:
            group = _rebuild(scene, node, {})
            children.append(bd.Compound(children=[*group.children, *heads],
                                        label=HARDWARE_GROUP))
        else:
            children.append(_rebuild(scene, node, {MAIN_HOST: host}))
    children.append(bd.Compound(children=covers, label=COVER_GROUP))

    meta.update({
        "host_volume_removed_mm3": sum(c["removed_mm3"] for c in meta["cuts"]),
        "host_volume_delta_default_precision_mm3": host_before.volume - host.volume,
        "hardware_group": HARDWARE_GROUP, "cover_group": COVER_GROUP,
        "hardware_labels": [h.label for h in heads],
        "cover_labels": [c.label for c in covers],
        "seat_count": len(built), "head_count": len(heads),
    })
    OUTPUT_METADATA.write_text(json.dumps(meta, indent=2, default=float) + "\n",
                               encoding="utf-8")
    return bd.Compound(children=children, label="halberd_r20_fin_seats")


def _materials():
    materials = copy.deepcopy(r19.MATERIALS)
    materials["assignments"].append({"targets": [f"#{COVER_GROUP}"],
                                     "material": "detail_paint"})
    return materials


MATERIALS = _materials()


@step(out="../STEP/halberd_r20_fin_seats.step", materials=MATERIALS)
def halberd_r20_fin_seats():
    return build_r20_fin_seats()


if __name__ == "__main__":
    halberd_r20_fin_seats()
