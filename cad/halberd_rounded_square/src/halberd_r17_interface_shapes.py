"""R17 gate-1 local fin-root and nozzle-lip interface prototypes.

All coordinates are millimetres in the saved R16 world frame.  This module
does not propagate the prototypes to other fins or modify the R16 model.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cadgen import build123d as bd, read_scene, srgb


ROOT = Path(__file__).resolve().parents[1]
BASELINE_STEP = ROOT / "STEP" / "halberd_r16.step"
REVIEW_FIXTURE_TRANSLATIONS = {
    "main_nozzle": (0.0, -130.0, 0.0),
    "booster_nozzle": (0.0, 130.0, 0.0),
}

FIN_PATCH_DEPTH = 0.80
FIN_INSET_DEPTH = 0.20
FIN_STRIP_THICKNESS = FIN_PATCH_DEPTH - FIN_INSET_DEPTH
FASTENER_SEAT_DEPTH = 1.02
FASTENER_TOP_RECESS = 0.18
FASTENER_HEAD_BOTTOM_RADIUS = 1.105
FASTENER_HEAD_TOP_RADIUS = 1.513
FASTENER_HEAD_HEIGHT = 0.4675
FASTENER_BORE_RADIUS = 1.156
FASTENER_COUNTERSINK_TOP_RADIUS = 1.802
FASTENER_COUNTERSINK_DEPTH = 0.6375
FASTENER_STEM_RADIUS = 1.105
FASTENER_SLOT_LENGTH = 2.125
FASTENER_SLOT_WIDTH = 0.425
FASTENER_SLOT_DEPTH = 0.25

METAL = "#87939B"
INSET = "#A7B0B7"


@dataclass
class InterfacePrototype:
    """One local prototype and the exact host cutters intended for integration."""

    key: str
    host_label: str
    host_before: object
    host_after: object
    cutters: tuple
    parts: tuple
    seat_cutters: tuple
    slot_cutters: tuple
    parameters: dict
    fixture_transform: object = None


def load_r16_parts():
    """Load native, world-placed R16 leaves without rebuilding or editing R16."""
    scene = read_scene(BASELINE_STEP)
    leaves = tuple(scene.leaves())
    parts = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in leaves}
    if len(parts) != len(leaves):
        raise ValueError("R16 baseline has duplicate leaf labels")
    return scene, parts


def _local_cylinder(radius, z0, z1):
    return bd.Cylinder(radius, z1 - z0,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .translate((0, 0, z0))


def _seat_tool_local():
    stem = _local_cylinder(FASTENER_BORE_RADIUS,
                           -FASTENER_SEAT_DEPTH,
                           -FASTENER_COUNTERSINK_DEPTH)
    sink_height = FASTENER_COUNTERSINK_DEPTH + 0.02
    sink = bd.Cone(FASTENER_BORE_RADIUS, FASTENER_COUNTERSINK_TOP_RADIUS,
                   sink_height,
                   align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .translate((0, 0, -FASTENER_COUNTERSINK_DEPTH))
    return stem + sink


def _slotted_head_local():
    stem_bottom = -FASTENER_SEAT_DEPTH
    head_bottom = -FASTENER_TOP_RECESS - FASTENER_HEAD_HEIGHT
    stem = _local_cylinder(FASTENER_STEM_RADIUS, stem_bottom, head_bottom)
    head = bd.Cone(FASTENER_HEAD_BOTTOM_RADIUS, FASTENER_HEAD_TOP_RADIUS,
                   FASTENER_HEAD_HEIGHT,
                   align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .translate((0, 0, head_bottom))
    screw = stem + head
    slot = bd.Box(FASTENER_SLOT_LENGTH, FASTENER_SLOT_WIDTH,
                  FASTENER_SLOT_DEPTH,
                  align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER)) \
        .translate((0, 0, -FASTENER_TOP_RECESS - FASTENER_SLOT_DEPTH / 2))
    return screw - slot, slot


def _oriented(shape, origin, outward, x_direction):
    plane = bd.Plane(origin=origin, x_dir=x_direction, z_dir=outward)
    return shape.moved(plane.location), plane


def _set_part(shape, label, color):
    shape.label = label
    shape.color = srgb(color)
    return shape


def fin_root_interface(host, host_label, *, face_index, center_uv,
                       screw_u, strip_length, strip_width):
    """Create one conformal fin-side inset and four short-stem slotted heads.

    The selected native STEP face supplies the actual location and normals.
    The returned ``cutters`` are ordered as the strip pocket followed by the
    four fastener seats; ``host_after`` is the exact native host minus them.
    ``center_uv`` and ``screw_u`` use build123d's normalized face parameters.
    """
    if len(screw_u) != 4:
        raise ValueError("A fin-root prototype requires exactly four screw sites")
    if len(host.solids()) != 1 or not host.is_valid:
        raise ValueError(f"{host_label}: expected one valid native host solid")
    face = host.faces()[face_index]
    u_center, v_center = center_uv
    center = face.position_at(u_center, v_center)
    outward = face.normal_at(u_center, v_center).normalized()
    inward = -outward

    # A bounded face crop retains the exact native ruled/spline host surface.
    mask_plane = bd.Plane(origin=center, x_dir=(1, 0, 0), z_dir=outward)
    mask = bd.Box(strip_length, strip_width, 40.0).moved(mask_plane.location)
    patch = face & mask
    if not patch or not patch.is_valid or len(patch.faces()) != 1:
        raise ValueError(f"{host_label}: native conformal strip patch is empty/invalid")
    strip_cutter = bd.Solid.extrude(patch, inward * FIN_PATCH_DEPTH)
    if strip_cutter.volume <= 0 or not strip_cutter.is_valid:
        raise ValueError(f"{host_label}: strip pocket cutter is invalid")

    seat_cutters = []
    slot_cutters = []
    heads = []
    local_seat = _seat_tool_local()
    local_head, local_slot = _slotted_head_local()
    screw_sites = []
    for index, u in enumerate(screw_u, 1):
        point = face.position_at(u, v_center)
        normal = face.normal_at(u, v_center).normalized()
        seat, plane = _oriented(local_seat, point, normal, (1, 0, 0))
        head, head_plane = _oriented(local_head, point, normal, (1, 0, 0))
        slot, _ = _oriented(local_slot, point, normal, (1, 0, 0))
        seat.label = f"{host_label}_seat_{index}"
        slot.label = f"{host_label}_slot_{index}"
        head.label = f"r17_{host_label.removesuffix('_1').removesuffix('_fairing')}_fastener_{index}"
        head.color = srgb(METAL)
        seat_cutters.append(seat)
        slot_cutters.append(slot)
        heads.append(head)
        screw_sites.append({
            "u": float(u),
            "point_mm": [point.X, point.Y, point.Z],
            "outward_normal": [normal.X, normal.Y, normal.Z],
            "seat_depth_mm": FASTENER_SEAT_DEPTH,
            "head_top_recess_mm": FASTENER_TOP_RECESS,
        })

    host_after = host - strip_cutter
    for seat in seat_cutters:
        host_after = host_after - seat
    host_after.label = f"{host_label}_r17_cut"
    host_after.color = host.color

    inset_start = patch.moved(bd.Location(inward * FIN_INSET_DEPTH))
    inset = bd.Solid.extrude(inset_start, inward * FIN_STRIP_THICKNESS)
    for seat in seat_cutters:
        inset = inset - seat
    inset = _set_part(inset, f"r17_{host_label}_inset_strip", INSET)

    cutters = (strip_cutter, *seat_cutters)
    return InterfacePrototype(
        key=host_label,
        host_label=host_label,
        host_before=host,
        host_after=host_after,
        cutters=cutters,
        parts=(inset, *heads),
        seat_cutters=tuple(seat_cutters),
        slot_cutters=tuple(slot_cutters),
        parameters={
            "face_index": face_index,
            "center_uv": list(center_uv),
            "patch_area_mm2": patch.area,
            "patch_bounds_mm": [patch.bounding_box().min.X,
                                patch.bounding_box().min.Y,
                                patch.bounding_box().min.Z,
                                patch.bounding_box().max.X,
                                patch.bounding_box().max.Y,
                                patch.bounding_box().max.Z],
            "strip_length_mm": strip_length,
            "strip_width_mm": strip_width,
            "strip_pocket_depth_mm": FIN_PATCH_DEPTH,
            "strip_inset_depth_mm": FIN_INSET_DEPTH,
            "screw_sites": screw_sites,
        },
    )


def cylinder_x(radius, x0, x1):
    return bd.Cylinder(radius, x1 - x0,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .rotate(bd.Axis.Y, 90).translate((x0, 0, 0))


def radial_point(x, radius, clock_degrees):
    import math
    angle = math.radians(clock_degrees)
    return bd.Vector(x, radius * math.sin(angle), radius * math.cos(angle))


def nozzle_lip_interface(host, host_label, *, key=None, mouth_x, cavity_radius,
                         outer_limit_radius, ring_cut_radii, ring_insert_radii,
                         screw_radius, clock_degrees=tuple(range(0, 360, 45))):
    """Create a recessed end-face annulus and eight aft-facing slotted heads."""
    prefix = key or host_label
    if len(clock_degrees) != 8:
        raise ValueError("A nozzle-rim prototype requires exactly eight fasteners")
    if len(host.solids()) != 1 or not host.is_valid:
        raise ValueError(f"{host_label}: expected one valid native host solid")
    cut_inner, cut_outer = ring_cut_radii
    insert_inner, insert_outer = ring_insert_radii
    if not cavity_radius < cut_inner < insert_inner < insert_outer < cut_outer:
        raise ValueError("Nozzle ring radii must be nested outside the open bore")

    ring_tool = cylinder_x(cut_outer, mouth_x, mouth_x + FIN_PATCH_DEPTH) \
        - cylinder_x(cut_inner, mouth_x, mouth_x + FIN_PATCH_DEPTH)
    ring_tool.label = f"{prefix}_r17_annular_seat"
    seat_cutters = []
    slot_cutters = []
    heads = []
    local_seat = _seat_tool_local()
    local_head, local_slot = _slotted_head_local()
    screw_sites = []
    for index, clock in enumerate(clock_degrees, 1):
        point = radial_point(mouth_x, screw_radius, clock)
        angle = __import__("math").radians(clock)
        tangent = (0, __import__("math").cos(angle), -__import__("math").sin(angle))
        outward = (-1, 0, 0)  # axial hardware faces aft from each stage lip
        seat, _ = _oriented(local_seat, point, outward, tangent)
        head, _ = _oriented(local_head, point, outward, tangent)
        slot, _ = _oriented(local_slot, point, outward, tangent)
        seat.label = f"{prefix}_r17_fastener_seat_{index}"
        slot.label = f"{prefix}_r17_fastener_slot_{index}"
        head.label = f"r17_{prefix}_fastener_{index}"
        head.color = srgb(METAL)
        seat_cutters.append(seat)
        slot_cutters.append(slot)
        heads.append(head)
        screw_sites.append({
            "clock_degrees": float(clock),
            "center_mm": [point.X, point.Y, point.Z],
            "radial_center_mm": screw_radius,
            "head_outer_radius_mm": FASTENER_HEAD_TOP_RADIUS,
            "seat_depth_mm": FASTENER_SEAT_DEPTH,
            "head_top_recess_mm": FASTENER_TOP_RECESS,
        })

    host_after = host - ring_tool
    for seat in seat_cutters:
        host_after = host_after - seat
    host_after.label = f"{prefix}_r17_cut"
    host_after.color = host.color

    ring = cylinder_x(insert_outer, mouth_x + FIN_INSET_DEPTH,
                      mouth_x + FIN_PATCH_DEPTH) \
        - cylinder_x(insert_inner, mouth_x + FIN_INSET_DEPTH,
                     mouth_x + FIN_PATCH_DEPTH)
    ring = _set_part(ring, f"r17_{prefix}_recessed_lip_ring", METAL)
    cutters = (ring_tool, *seat_cutters)
    return InterfacePrototype(
        key=prefix,
        host_label=host_label,
        host_before=host,
        host_after=host_after,
        cutters=cutters,
        parts=(ring, *heads),
        seat_cutters=tuple(seat_cutters),
        slot_cutters=tuple(slot_cutters),
        parameters={
            "mouth_x_mm": mouth_x,
            "cavity_radius_mm": cavity_radius,
            "outer_limit_radius_mm": outer_limit_radius,
            "ring_cut_radii_mm": list(ring_cut_radii),
            "ring_insert_radii_mm": list(ring_insert_radii),
            "ring_recess_depth_mm": FIN_PATCH_DEPTH,
            "ring_inset_mm": FIN_INSET_DEPTH,
            "screw_radius_mm": screw_radius,
            "screw_sites": screw_sites,
        },
    )


def build_r17_prototypes(baseline_parts=None):
    """Return the four requested local pilots in the unmodified R16 frame."""
    if baseline_parts is None:
        _, baseline_parts = load_r16_parts()
    return {
        "main_fin": fin_root_interface(
            baseline_parts["main_fin_1"], "main_fin_1", face_index=0,
            center_uv=(0.49, 0.25),
            screw_u=(0.31, 0.43, 0.55, 0.67),
            strip_length=52.0, strip_width=9.0),
        "booster_fin": fin_root_interface(
            baseline_parts["booster_fin_fairing_1"],
            "booster_fin_fairing_1", face_index=0,
            center_uv=(0.50, 0.55),
            screw_u=(0.35, 0.45, 0.55, 0.65),
            strip_length=52.0, strip_width=9.0),
        "main_nozzle": nozzle_lip_interface(
            baseline_parts["main_body_intake_r12"], "main_body_intake_r12",
            key="main_nozzle",
            mouth_x=-1123.3333333333, cavity_radius=65.0,
            outer_limit_radius=100.0, ring_cut_radii=(70.0, 73.0),
            ring_insert_radii=(70.25, 72.75), screw_radius=91.5),
        "booster_nozzle": nozzle_lip_interface(
            baseline_parts["booster_body"], "booster_body",
            key="booster_nozzle",
            mouth_x=-1685.0, cavity_radius=69.0,
            outer_limit_radius=82.0, ring_cut_radii=(70.0, 73.0),
            ring_insert_radii=(70.25, 72.75), screw_radius=78.4),
    }


def apply_fixture_transform(proto, fixture_transform):
    """Move every part and host cutter together using a build123d Location.

    The dimensions and probe coordinates in ``parameters`` remain expressed in
    the original R16 datum; ``fixture_transform`` records the occurrence pose.
    Call this only after a final builder has selected a specific occurrence.
    """
    if not isinstance(fixture_transform, bd.Location):
        raise TypeError("fixture_transform must be an explicit build123d Location")
    move = lambda shape: shape.moved(fixture_transform)
    return InterfacePrototype(
        key=proto.key,
        host_label=proto.host_label,
        host_before=move(proto.host_before),
        host_after=move(proto.host_after),
        cutters=tuple(move(shape) for shape in proto.cutters),
        parts=tuple(move(shape) for shape in proto.parts),
        seat_cutters=tuple(move(shape) for shape in proto.seat_cutters),
        slot_cutters=tuple(move(shape) for shape in proto.slot_cutters),
        parameters=proto.parameters,
        fixture_transform=fixture_transform,
    )


def _crop(shape, clip, label):
    result = shape & clip
    if not result or not result.is_valid:
        raise ValueError(f"Review crop {label} is empty or invalid")
    result.label = label
    result.color = shape.color
    return result


def _moved(shape, delta, label=None):
    result = shape.moved(bd.Location(delta))
    if label is not None:
        result.label = label
    return result


def build_review_artifact(kind):
    """Build one of three cropped review files and its exact saved-leaf map.

    The two nozzle coupons receive explicit fixture offsets in Y only; all
    source factories and host cutters remain in the original R16 coordinates.
    """
    scene, baseline = load_r16_parts()
    prototypes = build_r17_prototypes(baseline)
    expected = {}

    def coupon(name, proto, clip, context=(), shift=(0.0, 0.0, 0.0)):
        children = []
        host_crop = _crop(proto.host_after, clip,
                          f"r17_{name}_host_cut")
        children.append(host_crop)
        for source, label in context:
            children.append(_crop(source, clip, label))
        children.extend(proto.parts)
        placed = []
        for child in children:
            moved = _moved(child, shift)
            expected[moved.label] = moved
            placed.append(moved)
        group = bd.Compound(children=placed, label=f"r17_{name}_coupon")
        return group

    if kind == "main_fin":
        p = prototypes["main_fin"]
        clip = bd.Box(82.0, 76.0, 76.0).translate((-1031.0, 108.0, 111.0))
        assembly = coupon("main_fin", p, clip, (
            (baseline["main_body_intake_r12"], "r17_main_body_context"),))
    elif kind == "booster_fin":
        p = prototypes["booster_fin"]
        clip = bd.Box(82.0, 76.0, 76.0).translate((-1407.0, 108.0, 110.0))
        assembly = coupon("booster_fin", p, clip, (
            (baseline["booster_body"], "r17_booster_body_context"),))
    elif kind == "nozzles":
        groups = []
        main_clip = bd.Box(80.0, 220.0, 220.0).translate((-1090.0, 0.0, 0.0))
        main_context = (
            (baseline["main_nozzle_dark_recess"], "r17_main_nozzle_dark_recess_context"),
            (baseline["main_nozzle_dark_floor"], "r17_main_nozzle_dark_floor_context"),
        )
        groups.append(coupon("main_nozzle", prototypes["main_nozzle"],
                             main_clip, main_context,
                             REVIEW_FIXTURE_TRANSLATIONS["main_nozzle"]))

        booster_clip = bd.Box(90.0, 190.0, 190.0).translate((-1643.0, 0.0, 0.0))
        booster_context = (
            (baseline["booster_nozzle_dark_recess"], "r17_booster_nozzle_dark_recess_context"),
            (baseline["booster_nozzle_dark_floor"], "r17_booster_nozzle_dark_floor_context"),
        )
        groups.append(coupon("booster_nozzle", prototypes["booster_nozzle"],
                             booster_clip, booster_context,
                             REVIEW_FIXTURE_TRANSLATIONS["booster_nozzle"]))
        assembly = bd.Compound(children=groups, label="r17_nozzle_pair_review_coupons")
    else:
        raise ValueError(f"Unknown R17 review artifact: {kind}")

    return assembly, expected, prototypes, scene
