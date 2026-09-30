"""R19 full-body surface detail: joint screw rings and engraved panels.

Built on the saved R18 access STEP. The forward section (X=690-1085) reuses the
approved prototype construction and tables unchanged
(`halberd_r19_surface_proto.py`); this module adds the main body aft of X=690,
the stage joint ring (booster forward collar), the booster panels and the
booster aft joint (boattail start, X=-1520). See R19_SURFACE_DETAIL_DIRECTION.md.

Measured host facts used by the layout (tmp/r19_probe_*.py, 2026-09-28):
- Main body aft of X~690 and the booster are a rounded square: flats at
  +-100 mm with tangent half-width 30 mm, R~70 corners. Main-body corners carry
  the intake chines from X~600 aft, so main panels sit on the four flats only.
- Booster fin fairings sit on the corners X=-1483..-1123.3 and span clock
  36.5-53.5 deg (and the three rotated copies) at the stage-ring station.
- The booster boattail starts at X=-1520 (constant-X edge) and tapers to the
  nozzle rim at X=-1685.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from cadgen import build123d as bd, srgb

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from surface_detail import checked_cut, clock_frame  # noqa: E402
from surface_detail import seated_hardware, skin_point  # noqa: E402

from halberd_r16_shapes import fastener_seat
from halberd_r17_interface_shapes import (
    FASTENER_SEAT_DEPTH,
    _seat_tool_local,
    _slotted_head_local,
)
from halberd_r18_access import ACCESS_LABELS
from halberd_r18_access_build import materials_for_labels
from halberd_r18_access_shapes import (
    FASTENER_REMAINING_WALL_MIN,
    METAL,
    _extruded_skin_shell,
    _native_skin_patches,
    load_saved_parts,
    profile_prism,
)
import halberd_r19_surface_proto as proto


ROOT = Path(__file__).resolve().parents[1]
ACCESS_STEP = ROOT / "STEP" / "halberd_r18_access.step"
OUTPUT_METADATA = ROOT / "reviews" / "halberd_r19_surface.json"
MAIN_HOST = "main_body_intake_r12"
BOOSTER_HOST = "booster_body"

GROOVE_WIDTH = proto.GROOVE_WIDTH
GROOVE_DEPTH = proto.GROOVE_DEPTH
RING_PITCH = proto.RING_PITCH_DEGREES

# R16 nose-joint head/seat, expressed in a local skin frame (+Z outward, +X
# along the body, origin on the skin). The saved R16 head sits at X=1078 on
# the r=95 band at clock 0.
R16_HEAD_ORIGIN = (1078.0, 0.0, 95.0)
R16_SEAT_DEPTH = 1.5  # bore bottom at r=93.5 below the r=95 skin

# Stage joint: booster forward collar (joint face X=-1123.333).
STAGE_JOINT_X = -1123.3333333333
STAGE_RING_X = STAGE_JOINT_X - 7.0            # same 7 mm offset as the nose ring
STAGE_GROOVE_X = STAGE_JOINT_X - 25.0         # same 25 mm band as the nose groove
FAIRING_CLOCKS = (45.0, 135.0, 225.0, 315.0)
FAIRING_HALF_SPAN = 10.0  # measured 8.5 deg at the ring; 1.5 deg margin
# Booster aft joint: seam groove on the joint line, ring on the boattail.
AFT_JOINT_X = -1520.0
AFT_GROOVE_X = (AFT_JOINT_X, AFT_JOINT_X + GROOVE_WIDTH)
AFT_RING_X = AFT_JOINT_X - 7.0

_S45 = math.cos(math.radians(45.0))
_C30 = math.cos(math.radians(30.0))


def bolt4x(r):
    return ((-r * _S45, -r * _S45), (-r * _S45, r * _S45),
            (r * _S45, -r * _S45), (r * _S45, r * _S45))


def bolt4p(r):
    return ((-r, 0.0), (r, 0.0), (0.0, -r), (0.0, r))


def bolt3(r):
    return ((0.0, r), (-r * _C30, -r / 2.0), (r * _C30, -r / 2.0))


def pair(dx):
    return ((-dx, 0.0), (dx, 0.0))


def quad(dx, dt):
    return ((-dx, -dt), (-dx, dt), (dx, -dt), (dx, dt))


CENTRE = ((0.0, 0.0),)

# Layout per face, designed around the landmarks rather than a station matrix:
# forward equipment bay (X 450-690), a quiet mid-body, the intake station
# (X~-470..-350), the fin station (X -1075..-855), then the booster.
# (id, host, clock, centre X, centre tangent, shape, size..., screws)
#   rect: (length, width); round: (diameter,)
PANELS = (
    # --- main body, top (+Z, clock 0) ---
    ("T01", MAIN_HOST, 0.0, 615.0, 0.0, "rect", (90.0, 26.0), quad(38.0, 8.0)),
    ("T02", MAIN_HOST, 0.0, 520.0, 0.0, "round", (22.0,), bolt4x(7.5)),
    ("T03", MAIN_HOST, 0.0, 180.0, 0.0, "rect", (40.0, 14.0), pair(13.0)),
    ("T04", MAIN_HOST, 0.0, -410.0, 0.0, "rect", (120.0, 30.0),
     (*quad(52.0, 10.0), (0.0, -10.0), (0.0, 10.0))),
    ("T05", MAIN_HOST, 0.0, -520.0, 0.0, "round", (12.0,), CENTRE),
    ("T06", MAIN_HOST, 0.0, -960.0, 0.0, "rect", (150.0, 40.0),
     (*quad(67.0, 14.0), (0.0, -14.0), (0.0, 14.0))),
    ("T07", MAIN_HOST, 0.0, -1075.0, 0.0, "round", (18.0,), bolt3(5.5)),
    # --- main body, +Y side (clock 90); F04A 350-530, F04B -855..-725 ---
    ("S01", MAIN_HOST, 90.0, 640.0, 0.0, "rect", (64.0, 18.0), pair(25.0)),
    ("S02", MAIN_HOST, 90.0, 300.0, 0.0, "round", (20.0,), bolt3(6.5)),
    ("S03", MAIN_HOST, 90.0, -250.0, 0.0, "rect", (48.0, 16.0), pair(17.0)),
    ("S04", MAIN_HOST, 90.0, -480.0, 0.0, "round", (26.0,), bolt4x(9.5)),
    ("S05", MAIN_HOST, 90.0, -620.0, 0.0, "rect", (80.0, 22.0), quad(32.0, 6.0)),
    ("S06", MAIN_HOST, 90.0, -1010.0, 0.0, "rect", (56.0, 20.0), pair(21.0)),
    # --- main body, bottom (-Z, clock 180); F05 -110..390 at Y -22..-6 ---
    ("B01", MAIN_HOST, 180.0, 560.0, 0.0, "rect", (100.0, 24.0), quad(42.0, 7.0)),
    ("B02", MAIN_HOST, 180.0, 450.0, 0.0, "round", (14.0,), CENTRE),
    # B03 runs beside F05. Clock-180 tangent is -Y, and F05 occupies
    # Y=-22..-6 (tangent +6..+22), so B03 sits at tangent -17 (Y=+17).
    ("B03", MAIN_HOST, 180.0, 160.0, -17.0, "rect", (130.0, 14.0),
     ((-57.0, 0.0), (0.0, 0.0), (57.0, 0.0))),
    ("B04", MAIN_HOST, 180.0, -300.0, 0.0, "rect", (60.0, 20.0), pair(23.0)),
    ("B05", MAIN_HOST, 180.0, -420.0, 0.0, "round", (24.0,), bolt4p(8.5)),
    ("B06", MAIN_HOST, 180.0, -700.0, 0.0, "rect", (110.0, 22.0), quad(47.0, 6.0)),
    ("B07", MAIN_HOST, 180.0, -900.0, 0.0, "round", (18.0,), bolt3(5.5)),
    ("B08", MAIN_HOST, 180.0, -1040.0, 0.0, "rect", (34.0, 14.0), pair(11.0)),
    # --- main body, -Y side (clock 270); F03A 572-608 ---
    ("N01", MAIN_HOST, 270.0, 470.0, 0.0, "rect", (80.0, 20.0), pair(32.0)),
    ("N02", MAIN_HOST, 270.0, 250.0, 0.0, "round", (18.0,), bolt3(5.5)),
    ("N03", MAIN_HOST, 270.0, 20.0, 0.0, "rect", (56.0, 16.0), pair(21.0)),
    ("N04", MAIN_HOST, 270.0, -560.0, 0.0, "rect", (44.0, 26.0), quad(16.0, 8.0)),
    ("N05", MAIN_HOST, 270.0, -790.0, 0.0, "rect", (96.0, 22.0), quad(40.0, 6.0)),
    ("N06", MAIN_HOST, 270.0, -935.0, 0.0, "round", (20.0,), bolt4x(6.5)),
    ("N07", MAIN_HOST, 270.0, -1095.0, 0.0, "rect", (30.0, 14.0), pair(9.0)),
    # --- booster (flats; F10 top -1498..-1402, F03B -Y -1402..-1382) ---
    ("BT01", BOOSTER_HOST, 0.0, -1250.0, 0.0, "rect", (90.0, 24.0), quad(37.0, 7.0)),
    ("BT02", BOOSTER_HOST, 0.0, -1350.0, 0.0, "round", (14.0,), CENTRE),
    ("BS01", BOOSTER_HOST, 90.0, -1190.0, 0.0, "round", (24.0,), bolt4x(8.5)),
    ("BS02", BOOSTER_HOST, 90.0, -1380.0, 0.0, "rect", (120.0, 22.0), quad(52.0, 6.0)),
    ("BB01", BOOSTER_HOST, 180.0, -1215.0, 0.0, "rect", (44.0, 16.0), pair(15.0)),
    ("BB02", BOOSTER_HOST, 180.0, -1320.0, 0.0, "round", (18.0,), bolt3(5.5)),
    ("BB03", BOOSTER_HOST, 180.0, -1440.0, 0.0, "rect", (70.0, 26.0), quad(28.0, 8.0)),
    ("BN01", BOOSTER_HOST, 270.0, -1270.0, 0.0, "rect", (76.0, 18.0), pair(30.0)),
    ("BN02", BOOSTER_HOST, 270.0, -1465.0, 0.0, "rect", (30.0, 14.0), pair(9.0)),
    # --- booster boattail (tapered skin aft of the aft joint) ---
    ("BA01", BOOSTER_HOST, 90.0, -1595.0, 0.0, "round", (18.0,), bolt3(5.5)),
    ("BA02", BOOSTER_HOST, 270.0, -1605.0, 0.0, "rect", (28.0, 12.0), pair(8.0)),
)


def _prefix(host_label):
    return "main_r19" if host_label == MAIN_HOST else "booster_r19"


def _stage_ring_clocks():
    clocks = []
    for index in range(int(round(360.0 / RING_PITCH))):
        clock = index * RING_PITCH
        if any(abs((clock - f + 180.0) % 360.0 - 180.0) < FAIRING_HALF_SPAN
               for f in FAIRING_CLOCKS):
            continue
        clocks.append(clock)
    return tuple(clocks)


def _aft_ring_clocks():
    return tuple(i * RING_PITCH for i in range(int(round(360.0 / RING_PITCH))))


STAGE_RING_CLOCKS = _stage_ring_clocks()
AFT_RING_CLOCKS = _aft_ring_clocks()


def ring_label(ring, clock):
    return f"booster_r19_{ring}_ring_fastener_{int(round(clock)):03d}"


def planned_labels():
    labels = list(proto._planned_labels())
    labels = [l for l in labels if l not in (proto.HOST_LABEL,)]
    for panel_id, host, *_rest, screws in PANELS:
        labels.extend(f"{_prefix(host)}_{panel_id}_fastener_{i}"
                      for i in range(1, len(screws) + 1))
    labels.extend(ring_label("stage", c) for c in STAGE_RING_CLOCKS)
    labels.extend(ring_label("aft", c) for c in AFT_RING_CLOCKS)
    return labels


def r19_materials():
    materials = materials_for_labels(ACCESS_LABELS, include_all_base=True)
    metal = sorted(f"#{l}" for l in planned_labels()
                   if l.startswith(("main_r19_", "booster_r19_")))
    materials["assignments"].append({"targets": metal, "material": "detail_metal"})
    return materials


# --- construction -----------------------------------------------------------

def _r16_local_tools(saved):
    ox, oy, oz = R16_HEAD_ORIGIN
    to_local = bd.Location((-ox, -oy, -oz))
    head = saved["main_joint_fastener_1"].moved(to_local)
    seat = fastener_seat(0.0).moved(to_local)
    return seat, head


def joint_ring(host, ring, x, clocks, seat_tool, head_tool):
    seats, heads, sites = [], [], {}
    for clock in clocks:
        s, h, site = seated_hardware(
            host, x, clock, ((0.0, 0.0),), seat_tool, head_tool,
            seat_depth=R16_SEAT_DEPTH, min_remaining_wall=FASTENER_REMAINING_WALL_MIN,
            label_prefix=f"booster_r19_{ring}_ring", color=srgb(METAL))
        head = h[0]
        head.label = ring_label(ring, clock)
        seats.append(s[0])
        heads.append(head)
        sites[f"{clock:.1f}"] = site[0]
    return tuple(seats), tuple(heads), sites


def _sector_prism(x0, x1, clock_lo, clock_hi, radius=300.0, steps=8):
    points = [(0.0, 0.0)]
    for i in range(steps + 1):
        a = math.radians(clock_lo + (clock_hi - clock_lo) * i / steps)
        points.append((radius * math.sin(a), radius * math.cos(a)))
    wire = bd.Wire.make_polygon([(x0, y, z) for y, z in points], close=True)
    return bd.Solid.extrude(bd.Face(wire), bd.Vector(x1 - x0, 0.0, 0.0))


def section_groove(host, x0, x1, depth, skip_clocks=(), skip_half_span=0.0, label=""):
    """Uniform-depth circumferential groove on a prismatic stretch X=x0..x1.

    The outer section wire at x0 is offset inward by ``depth`` in its own plane
    and the ring face is extruded to x1; optional clock sectors are left uncut.
    """
    slab = host & bd.Box(x1 - x0, 600.0, 600.0).translate(((x0 + x1) / 2.0, 0.0, 0.0))
    planar = [f for f in slab.faces()
              if f.geom_type == bd.GeomType.PLANE and abs(f.center().X - x0) < 1e-6
              and abs(abs(f.normal_at().X) - 1.0) < 1e-9]
    if len(planar) != 1:
        raise ValueError((label, "expected one section face at groove start", len(planar)))
    outer = planar[0].outer_wire()
    inner = outer.offset_2d(-depth)
    ring = bd.Face(outer) - bd.Face(inner)
    cutter = bd.Solid.extrude(ring, bd.Vector(x1 - x0, 0.0, 0.0))
    for clock in skip_clocks:
        cutter = cutter - _sector_prism(x0 - 1.0, x1 + 1.0,
                                        clock - skip_half_span, clock + skip_half_span)
    cutter.label = label
    return cutter


def _outline(shape, size):
    if shape == "round":
        return bd.Wire.make_circle(size[0] / 2.0)
    return proto._panel_wire(*size)


def engraved_panel(host, panel_id, host_label, clock, x, t0, shape, size, screws):
    """Prototype engraved-panel construction, generalised to a tangent offset."""
    length, width = (size[0], size[0]) if shape == "round" else size
    center = skin_point(host, x, t0, clock)
    origin, outward = center["point"], center["normal"].normalized()
    outer = _outline(shape, size)
    ring = bd.Face(outer) - bd.Face(outer.offset_2d(-GROOVE_WIDTH))
    mask = profile_prism(ring, origin, outward, None)
    faces = []
    for dx in (-length / 2.0, 0.0, length / 2.0):
        for dt in (-width / 2.0, 0.0, width / 2.0):
            face = skin_point(host, x + dx, t0 + dt, clock)["face"]
            if not any(face.is_same(existing) for existing in faces):
                faces.append(face)
    patches = _native_skin_patches(tuple(faces), mask, outward)
    patch_area = sum(p.area for p in patches)
    if patch_area < ring.area * 0.99:
        raise ValueError((panel_id, "native skin clipped the panel outline",
                          ring.area, patch_area))
    groove = _extruded_skin_shell(patches, host, outward, 0.0, GROOVE_DEPTH,
                                  f"{panel_id} groove")
    local_head, _slot = _slotted_head_local()
    seats, heads, sites = seated_hardware(
        host, x, clock, tuple((dx, t0 + dt) for dx, dt in screws),
        _seat_tool_local(), local_head, seat_depth=FASTENER_SEAT_DEPTH,
        min_remaining_wall=FASTENER_REMAINING_WALL_MIN,
        label_prefix=f"{_prefix(host_label)}_{panel_id}", color=srgb(METAL))
    return (groove, *seats), heads, {
        "host": host_label, "clock_degrees": clock, "center_x_mm": x,
        "center_tangent_mm": t0, "outline": "circle" if shape == "round" else "chamfered_rect",
        "length_mm": length, "width_mm": width,
        "groove_width_mm": GROOVE_WIDTH, "groove_depth_mm": GROOVE_DEPTH,
        "groove_volume_mm3": groove.volume, "outline_patch_area_mm2": patch_area,
        "center_normal": [outward.X, outward.Y, outward.Z],
        "screw_sites": list(sites),
    }


def _forward_section(host, saved):
    """Exactly the approved prototype steps, applied to the full-length host."""
    ring_seats, ring_heads = proto._ring_fasteners(saved["main_joint_fastener_1"])
    slab_box = bd.Box(100.0, 400.0, 400.0).translate((proto.RING_SLAB_X + 50.0, 0.0, 0.0))
    slab = host & slab_box
    rest = host - slab_box
    for seat in ring_seats:
        slab = checked_cut(slab, seat)
    band = slab & bd.Box(GROOVE_WIDTH, 400.0, 400.0).translate(
        (proto.RING_SLAB_X + GROOVE_WIDTH / 2.0, 0.0, 0.0))
    band_radius = max(band.bounding_box().max.Y, band.bounding_box().max.Z)
    scale = 1.0 - GROOVE_DEPTH / band_radius
    seam_groove = band - band.scale((1.0, scale, scale), about=(0.0, 0.0, 0.0))
    slab = checked_cut(slab, seam_groove)
    host = (rest + slab).clean()
    if not host.is_valid or len(host.solids()) != 1:
        raise ValueError("forward ring slab rejoin is invalid or split")

    cutters, heads, data = [], list(ring_heads), {}
    for panel_id, clock, x, length, width, screws in proto.PANELS:
        c, h, d = proto.engraved_panel(host, panel_id, clock, x, length, width, screws)
        d.update(host=MAIN_HOST, center_tangent_mm=0.0, outline="chamfered_rect")
        cutters.extend(c)
        heads.extend(h)
        data[panel_id] = d
    for panel_id, clock, x, diameter, screws in proto.ROUND_PANELS:
        c, h, d = proto.engraved_panel(host, panel_id, clock, x, diameter, diameter,
                                       screws, outer=bd.Wire.make_circle(diameter / 2.0))
        d.update(host=MAIN_HOST, center_tangent_mm=0.0, outline="circle")
        cutters.extend(c)
        heads.extend(h)
        data[panel_id] = d
    for cutter in cutters:
        host = checked_cut(host, cutter)
    seam = {"x_mm": [proto.RING_SLAB_X, proto.RING_SLAB_X + GROOVE_WIDTH],
            "depth_mm": GROOVE_DEPTH, "volume_mm3": seam_groove.volume,
            "construction": "radial scale of the joint band (prototype)"}
    return host, heads, data, seam, [h.label for h in ring_heads]


def build_r19_surface():
    scene, saved = load_saved_parts(ACCESS_STEP)
    main, booster = saved[MAIN_HOST], saved[BOOSTER_HOST]
    main_before, booster_before = main.volume, booster.volume

    # Forward section first (slab work before other Booleans touch the host).
    main, new_parts, panel_data, forward_seam, forward_ring = _forward_section(main, saved)

    # Booster joint rings and seams.
    seat_tool, head_tool = _r16_local_tools(saved)
    stage_seats, stage_heads, stage_sites = joint_ring(
        booster, "stage", STAGE_RING_X, STAGE_RING_CLOCKS, seat_tool, head_tool)
    aft_seats, aft_heads, aft_sites = joint_ring(
        booster, "aft", AFT_RING_X, AFT_RING_CLOCKS, seat_tool, head_tool)
    stage_groove = section_groove(
        booster, STAGE_GROOVE_X - GROOVE_WIDTH, STAGE_GROOVE_X, GROOVE_DEPTH,
        FAIRING_CLOCKS, FAIRING_HALF_SPAN, "booster_r19_stage_seam_groove")
    aft_groove = section_groove(booster, *AFT_GROOVE_X, GROOVE_DEPTH,
                                label="booster_r19_aft_seam_groove")
    for cutter in (*stage_seats, *aft_seats, stage_groove, aft_groove):
        booster = checked_cut(booster, cutter)
    new_parts.extend(stage_heads)
    new_parts.extend(aft_heads)

    # Panels on the main body aft of the forward section and on the booster.
    hosts = {MAIN_HOST: main, BOOSTER_HOST: booster}
    for panel_id, host_label, clock, x, t0, shape, size, screws in PANELS:
        cutters, heads, data = engraved_panel(hosts[host_label], panel_id, host_label,
                                              clock, x, t0, shape, size, screws)
        for cutter in cutters:
            hosts[host_label] = checked_cut(hosts[host_label], cutter)
        new_parts.extend(heads)
        panel_data[panel_id] = data
    main, booster = hosts[MAIN_HOST], hosts[BOOSTER_HOST]

    for label, host, before in ((MAIN_HOST, main, main_before),
                                (BOOSTER_HOST, booster, booster_before)):
        if not host.is_valid or len(host.solids()) != 1 or host.volume >= before:
            raise ValueError((label, "R19 cuts invalidated or failed to cut the host"))
        host.label, host.color = label, saved[label].color
        for head in new_parts:
            if host.is_inside(head.center()):
                raise ValueError((head.label, "fastener centre lies inside", label))

    parts = [main, booster]
    parts.extend(p for l, p in saved.items() if l not in (MAIN_HOST, BOOSTER_HOST))
    parts.extend(new_parts)
    for part in parts:
        if not part or not part.is_valid or len(part.solids()) != 1 or part.volume <= 1e-8:
            raise ValueError((part.label, "R19 part is empty, invalid or not one solid"))
    labels = [p.label for p in parts]
    if len(labels) != len(set(labels)):
        raise ValueError("duplicate R19 labels")
    expected = set(planned_labels()) | set(saved)
    if set(labels) != expected:
        raise ValueError(("R19 labels differ from the plan",
                          sorted(set(labels) ^ expected)))

    OUTPUT_METADATA.write_text(json.dumps({
        "gate": "R19 full-body surface detail (awaiting user visual review)",
        "source_step": "STEP/halberd_r18_access.step",
        "source_document_hash": scene.document_hash,
        "host_volume_removed_mm3": {MAIN_HOST: main_before - main.volume,
                                    BOOSTER_HOST: booster_before - booster.volume},
        "rings": {
            "nose": {"x_mm": 1078.0, "pitch_degrees": RING_PITCH,
                     "kept_r16_clocks": list(proto.R16_CLOCKS), "new_fasteners": forward_ring},
            "stage": {"x_mm": STAGE_RING_X, "pitch_degrees": RING_PITCH,
                      "clocks": list(STAGE_RING_CLOCKS),
                      "skipped_fairing_clocks": list(FAIRING_CLOCKS),
                      "skip_half_span_degrees": FAIRING_HALF_SPAN, "sites": stage_sites},
            "aft": {"x_mm": AFT_RING_X, "pitch_degrees": RING_PITCH,
                    "clocks": list(AFT_RING_CLOCKS), "sites": aft_sites},
        },
        "seam_grooves": {
            "nose": forward_seam,
            "stage": {"x_mm": [STAGE_GROOVE_X - GROOVE_WIDTH, STAGE_GROOVE_X],
                      "depth_mm": GROOVE_DEPTH, "volume_mm3": stage_groove.volume,
                      "skipped_fairing_clocks": list(FAIRING_CLOCKS),
                      "skip_half_span_degrees": FAIRING_HALF_SPAN,
                      "construction": "section wire offset (uniform depth)"},
            "aft": {"x_mm": list(AFT_GROOVE_X), "depth_mm": GROOVE_DEPTH,
                    "volume_mm3": aft_groove.volume,
                    "construction": "section wire offset (uniform depth)"},
        },
        "panels": panel_data,
        "labels": labels,
    }, indent=2) + "\n", encoding="utf-8")
    return bd.Compound(children=parts, label="Halberd_R19_Surface")
