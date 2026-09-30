"""R19 prototype: nose-joint radial screw ring and Kris-density engraved panels.

Forward main-body section only (X=690-1100), built on the saved R18 access STEP.
See R19_SURFACE_DETAIL_DIRECTION.md. Not propagated to other sections.
"""
from __future__ import annotations

import json
import math
import sys
from copy import deepcopy
from pathlib import Path

from cadgen import build123d as bd, srgb, step

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from surface_detail import checked_cut as _checked_cut  # noqa: E402
from surface_detail import clock_frame as _clock_frame  # noqa: E402
from surface_detail import seated_hardware, skin_point  # noqa: E402

from halberd_r16_shapes import fastener_seat
from halberd_r17_interface_shapes import (
    FASTENER_BORE_RADIUS,
    FASTENER_COUNTERSINK_DEPTH,
    FASTENER_COUNTERSINK_TOP_RADIUS,
    FASTENER_SEAT_DEPTH,
    _local_cylinder,
    _seat_tool_local,
    _slotted_head_local,
)
from halberd_r18_access_shapes import (
    BODY_PAINT,
    FASTENER_REMAINING_WALL_MIN,
    METAL,
    _extruded_skin_shell,
    _native_skin_patches,
    load_saved_parts,
    profile_prism,
)
from halberd_r18_layout_base import MATERIALS as R18_BASE_MATERIALS


ROOT = Path(__file__).resolve().parents[1]
ACCESS_STEP = ROOT / "STEP" / "halberd_r18_access.step"
OUTPUT_METADATA = ROOT / "reviews" / "halberd_r19_surface_proto.json"
MAIN_HOST = "main_body_intake_r12"
HOST_LABEL = "main_body_intake_r12_r19_proto"
CROP_X = (690.0, 1100.0)

RING_PITCH_DEGREES = 15.0
RING_SLAB_X = 1060.0
R16_CLOCKS = (0.0, 90.0, 180.0, 270.0)
GROOVE_WIDTH = 0.40
GROOVE_DEPTH = 0.40
CORNER_CHAMFER = 2.5

# Staggered per clock (Kris-style density); F02 keeps the +Z face.
# (id, clock, axial centre X, length, width, screw offsets (dx, dt))
PANELS = (
    ("P01", 45.0, 1025.0, 36.0, 14.0, ((-11.0, 0.0), (11.0, 0.0))),
    ("P02", 90.0, 765.0, 72.0, 20.0, ((-28.0, 0.0), (28.0, 0.0))),
    ("P03", 90.0, 975.0, 44.0, 16.0, ((-15.0, 0.0), (15.0, 0.0))),
    ("P04", 135.0, 930.0, 62.0, 16.0, ((-23.0, 0.0), (23.0, 0.0))),
    ("P05", 180.0, 865.0, 112.0, 22.0,
     ((-47.0, -6.0), (-47.0, 6.0), (47.0, -6.0), (47.0, 6.0))),
    ("P06", 225.0, 735.0, 42.0, 16.0, ((-14.0, 0.0), (14.0, 0.0))),
    ("P07", 270.0, 800.0, 56.0, 18.0, ((-20.0, 0.0), (20.0, 0.0))),
    ("P08", 270.0, 1000.0, 30.0, 14.0, ((-9.0, 0.0), (9.0, 0.0))),
    ("P09", 315.0, 745.0, 48.0, 14.0, ((-17.0, 0.0), (17.0, 0.0))),
)

# Round engraved panels, each with its own hardware pattern (user request
# 2026-09-28). (id, clock, axial centre X, diameter, screw offsets (dx, dt))
_S45 = 10.5 * math.cos(math.radians(45.0))
ROUND_PANELS = (
    ("C01", 90.0, 870.0, 28.0,
     ((-_S45, -_S45), (-_S45, _S45), (_S45, -_S45), (_S45, _S45))),
    ("C02", 225.0, 900.0, 20.0,
     ((0.0, 6.5), (-6.5 * math.cos(math.radians(30.0)), -3.25),
      (6.5 * math.cos(math.radians(30.0)), -3.25))),
    ("C03", 315.0, 960.0, 14.0, ((0.0, 0.0),)),
    ("C04", 180.0, 1010.0, 24.0, ((-8.5, 0.0), (8.5, 0.0), (0.0, -8.5), (0.0, 8.5))),
)


def _panel_wire(length, width):
    hx, hy, c = length / 2.0, width / 2.0, CORNER_CHAMFER
    points = [(-hx + c, -hy), (hx - c, -hy), (hx, -hy + c), (hx, hy - c),
              (hx - c, hy), (-hx + c, hy), (-hx, hy - c), (-hx, -hy + c)]
    return bd.Wire.make_polygon([(x, y, 0.0) for x, y in points], close=True)


SEAT_EXTENSION = 0.30


def seat_tool_extended():
    """R17 seat whose countersink cone continues 0.3 mm above the skin.

    The R17 tool's top rim sits 0.02 mm above the skin, so on curved skin
    the cut curve runs along that rim and OCC can silently skip the cut
    (seen on the booster's rounded corners). Continuing the cone moves the
    intersection mid-cone; the seat below the skin is unchanged.
    """
    slope = (FASTENER_COUNTERSINK_TOP_RADIUS - FASTENER_BORE_RADIUS) /         (FASTENER_COUNTERSINK_DEPTH + 0.02)
    top = FASTENER_COUNTERSINK_TOP_RADIUS + (SEAT_EXTENSION - 0.02) * slope
    stem = _local_cylinder(FASTENER_BORE_RADIUS, -FASTENER_SEAT_DEPTH,
                           -FASTENER_COUNTERSINK_DEPTH)
    sink = bd.Cone(FASTENER_BORE_RADIUS, top, FASTENER_COUNTERSINK_DEPTH + SEAT_EXTENSION,
                   align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))         .translate((0, 0, -FASTENER_COUNTERSINK_DEPTH))
    return stem + sink


def slotted_hardware(host, panel_id, center_x, clock, screw_coordinates, stage="main",
                     extended_seat=False):
    """R17 short slotted heads seated on ray-measured skin (R18 construction)."""
    local_head, _local_slot = _slotted_head_local()
    seat_tool = seat_tool_extended() if extended_seat else _seat_tool_local()
    return seated_hardware(
        host, center_x, clock, screw_coordinates, seat_tool, local_head,
        seat_depth=FASTENER_SEAT_DEPTH, min_remaining_wall=FASTENER_REMAINING_WALL_MIN,
        label_prefix=f"{stage}_r19_{panel_id}", color=srgb(METAL))


def _skin_faces(host, x, clock, length, width, tangent_offset=0.0):
    faces = []
    for dx in (-length / 2.0, 0.0, length / 2.0):
        for dt in (-width / 2.0, 0.0, width / 2.0):
            face = skin_point(host, x + dx, tangent_offset + dt, clock)["face"]
            if not any(face.is_same(existing) for existing in faces):
                faces.append(face)
    return tuple(faces)


def engraved_panel(host, panel_id, clock, x, length, width, screws, outer=None,
                   tangent_offset=0.0, stage="main", extended_seat=False):
    """Cut one hairline panel outline into native skin and seat its screws.

    ``host`` may be a local crop of the owner body (measurement and groove
    extrusion only need nearby skin); cut the returned tools from the owner.
    ``tangent_offset`` shifts the panel sideways across its face.
    """
    _, tangent = _clock_frame(clock)
    center = skin_point(host, x, tangent_offset, clock)
    origin, outward = center["point"], center["normal"].normalized()
    if outer is None:
        outer = _panel_wire(length, width)
    ring = bd.Face(outer) - bd.Face(outer.offset_2d(-GROOVE_WIDTH))
    mask = profile_prism(ring, origin, outward, tangent)
    # Sample rays near the outline edge can land on neighbouring faces that
    # the outline never reaches; the R18 clip helper needs touching faces only.
    faces = [f for f in _skin_faces(host, x, clock, length, width, tangent_offset)
             if f & mask]
    patches = _native_skin_patches(faces, mask, outward)
    patch_area = sum(p.area for p in patches)
    if patch_area < ring.area * 0.99:
        raise ValueError((panel_id, "native skin clipped the panel outline",
                          ring.area, patch_area))
    groove = _extruded_skin_shell(patches, host, outward, 0.0, GROOVE_DEPTH,
                                  f"{panel_id} groove")
    shifted = [(dx, dt + tangent_offset) for dx, dt in screws]
    seats, heads, sites = slotted_hardware(host, panel_id, x, clock, shifted, stage,
                                           extended_seat)
    return (groove, *seats), heads, {
        "clock_degrees": clock, "center_x_mm": x, "tangent_offset_mm": tangent_offset,
        "length_mm": length,
        "width_mm": width, "groove_width_mm": GROOVE_WIDTH,
        "groove_depth_mm": GROOVE_DEPTH, "groove_volume_mm3": groove.volume,
        "outline_patch_area_mm2": patch_area,
        "center_normal_dot_radial": outward.dot(_clock_frame(clock)[0]),
        "screw_sites": list(sites),
    }


def _ring_fasteners(template):
    heads, seats = [], []
    seat_template = fastener_seat(0.0)
    steps = int(round(360.0 / RING_PITCH_DEGREES))
    for index in range(steps):
        clock = index * RING_PITCH_DEGREES
        if any(abs(clock - kept) < 1e-6 for kept in R16_CLOCKS):
            continue  # accepted R16 fasteners stay as saved
        # Head and seat share one transform so the seat cannot land mirrored.
        placement = bd.Location((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -clock)
        head = template.moved(placement)
        seat = seat_template.moved(placement)
        center = head.center()
        measured = math.degrees(math.atan2(center.Y, center.Z)) % 360.0
        if abs((measured - clock + 180.0) % 360.0 - 180.0) > 0.05:
            raise ValueError(("ring fastener placement clock mismatch", clock, measured))
        head.label = f"main_r19_joint_ring_fastener_{int(clock):03d}"
        head.color = srgb(METAL)
        heads.append(head)
        seats.append(seat)
    return tuple(seats), tuple(heads)


def _crop_box(bounds):
    return bd.Box(CROP_X[1] - CROP_X[0], 400.0, 400.0).translate(
        ((CROP_X[0] + CROP_X[1]) / 2.0, 0.0, 0.0))


def build_r19_surface_proto():
    scene, saved = load_saved_parts(ACCESS_STEP)
    clip = _crop_box(CROP_X)
    host = saved[MAIN_HOST] & clip
    if not host or not host.is_valid or len(host.solids()) != 1:
        raise ValueError("forward host crop is empty, invalid or split")

    ring_seats, ring_heads = _ring_fasteners(saved["main_joint_fastener_1"])
    new_parts = list(ring_heads)

    before = host.volume
    # OCC silently no-ops these seat cuts on the long host near the joint
    # pocket, but not on a local slab, so cut them there and rejoin. The slab
    # box overruns the crop end so no box face is coplanar with it.
    slab_box = bd.Box(100.0, 400.0, 400.0).translate((RING_SLAB_X + 50.0, 0.0, 0.0))
    slab = host & slab_box
    rest = host - slab_box
    for seat in ring_seats:
        slab = _checked_cut(slab, seat)
    # The rejoin can keep a skin edge at the split, so make it a real seam: a
    # conformal groove (skin band minus a copy scaled radially about X) whose
    # aft wall is the split plane. Depth is GROOVE_DEPTH at the band's largest
    # radius and within 0.001 mm of it around the rest of the section.
    band = slab & bd.Box(GROOVE_WIDTH, 400.0, 400.0).translate(
        (RING_SLAB_X + GROOVE_WIDTH / 2.0, 0.0, 0.0))
    band_radius = max(band.bounding_box().max.Y, band.bounding_box().max.Z)
    scale = 1.0 - GROOVE_DEPTH / band_radius
    seam_groove = band - band.scale((1.0, scale, scale), about=(0.0, 0.0, 0.0))
    seam_groove.label = "main_r19_joint_seam_groove"
    slab = _checked_cut(slab, seam_groove)
    host = (rest + slab).clean()
    if not host.is_valid or len(host.solids()) != 1:
        raise ValueError("ring slab rejoin is invalid or split")

    cutters, panel_data = [], {}
    for panel_id, clock, x, length, width, screws in PANELS:
        panel_cutters, heads, data = engraved_panel(host, panel_id, clock, x,
                                                    length, width, screws)
        cutters.extend(panel_cutters)
        new_parts.extend(heads)
        panel_data[panel_id] = data
    for panel_id, clock, x, diameter, screws in ROUND_PANELS:
        panel_cutters, heads, data = engraved_panel(
            host, panel_id, clock, x, diameter, diameter, screws,
            outer=bd.Wire.make_circle(diameter / 2.0))
        data["outline"] = "circle"
        cutters.extend(panel_cutters)
        new_parts.extend(heads)
        panel_data[panel_id] = data
    # Sequential checked cuts: a single multi-tool OCC cut over-removed
    # material here (331 vs <=322 mm3 possible) and was not faster.
    for cutter in cutters:
        host = _checked_cut(host, cutter)
    if not host.is_valid or len(host.solids()) != 1 or host.volume >= before:
        raise ValueError("prototype cuts invalidated or failed to cut the host")
    # Every head sits in its seat void; the independent checker repeats this
    # with exact Boolean overlaps on the saved STEP.
    for head in new_parts:
        if host.is_inside(head.center()):
            raise ValueError((head.label, "fastener centre lies inside the host skin"))
    host.label = HOST_LABEL
    host.color = saved[MAIN_HOST].color

    kept = []
    for label, part in saved.items():
        if label == MAIN_HOST:
            continue
        box = part.bounding_box()
        if box.max.X <= CROP_X[0] or box.min.X >= CROP_X[1]:
            continue
        if box.min.X < CROP_X[0] or box.max.X > CROP_X[1]:
            cropped = part & clip
            cropped.label, cropped.color = label, part.color
            part = cropped
        kept.append(part)

    parts = [host, *kept, *new_parts]
    for part in parts:
        if not part or not part.is_valid or len(part.solids()) != 1 or part.volume <= 1e-8:
            raise ValueError((part.label, "prototype part is empty, invalid or not one solid"))
    labels = [p.label for p in parts]
    if len(labels) != len(set(labels)):
        raise ValueError("duplicate prototype labels")

    OUTPUT_METADATA.write_text(json.dumps({
        "gate": "R19 forward-section prototype (not approved for propagation)",
        "source_step": "STEP/halberd_r18_access.step",
        "source_document_hash": scene.document_hash,
        "crop_x_mm": list(CROP_X),
        "host_volume_removed_mm3": before - host.volume,
        "ring": {"pitch_degrees": RING_PITCH_DEGREES,
                 "kept_r16_clocks": list(R16_CLOCKS),
                 "new_fasteners": [h.label for h in ring_heads]},
        "joint_seam_groove": {"x_mm": [RING_SLAB_X, RING_SLAB_X + GROOVE_WIDTH],
                              "depth_mm": GROOVE_DEPTH,
                              "volume_mm3": seam_groove.volume},
        "panels": panel_data,
        "labels": labels,
    }, indent=2) + "\n", encoding="utf-8")
    return bd.Compound(children=parts, label="Halberd_R19_Surface_Proto_Forward")


def proto_materials(labels):
    materials = deepcopy(R18_BASE_MATERIALS)
    selected = set(labels)
    assignments = []
    for assignment in materials["assignments"]:
        targets = []
        for target in assignment["targets"]:
            source = target.lstrip("#")
            if source in selected:
                targets.append(target)
            elif source == MAIN_HOST:
                targets.append(f"#{HOST_LABEL}")
        if targets:
            entry = deepcopy(assignment)
            entry["targets"] = targets
            assignments.append(entry)
    metal = sorted(f"#{l}" for l in selected
                   if l.startswith(("main_r19_", "main_r18_F02_fastener_")))
    paint = sorted(f"#{l}" for l in selected if l == "main_r18_F02_cover")
    if paint:
        assignments.append({"targets": paint, "material": "detail_paint"})
    if metal:
        assignments.append({"targets": metal, "material": "detail_metal"})
    materials["assignments"] = assignments
    return materials


def _planned_labels():
    labels = [HOST_LABEL, "main_ogive", "main_joint_liner_1",
              *(f"main_joint_fastener_{i}" for i in range(1, 5)),
              "main_r18_F02_cover", *(f"main_r18_F02_fastener_{i}" for i in range(1, 5))]
    for panel_id, *_, screws in (*PANELS, *ROUND_PANELS):
        labels.extend(f"main_r19_{panel_id}_fastener_{i}" for i in range(1, len(screws) + 1))
    steps = int(round(360.0 / RING_PITCH_DEGREES))
    labels.extend(f"main_r19_joint_ring_fastener_{int(i * RING_PITCH_DEGREES):03d}"
                  for i in range(steps)
                  if not any(abs(i * RING_PITCH_DEGREES - c) < 1e-6 for c in R16_CLOCKS))
    return labels


MATERIALS = proto_materials(_planned_labels())


@step(out="../STEP/halberd_r19_surface_proto_forward.step", materials=MATERIALS)
def halberd_r19_surface_proto_forward():
    return build_r19_surface_proto()


if __name__ == "__main__":
    halberd_r19_surface_proto_forward()
