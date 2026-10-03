"""R18 access-feature geometry helpers, built from the approved R18 layout."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from cadgen import build123d as bd, read_scene, srgb
try:
    from cadgen import declare_input
except ImportError:  # cadgen >= 0.7.10 traces input reads itself
    def declare_input(_path):
        return None

from halberd_r17_interface_shapes import (
    FASTENER_BORE_RADIUS,
    FASTENER_COUNTERSINK_DEPTH,
    FASTENER_COUNTERSINK_TOP_RADIUS,
    FASTENER_HEAD_BOTTOM_RADIUS,
    FASTENER_HEAD_HEIGHT,
    FASTENER_HEAD_TOP_RADIUS,
    FASTENER_SEAT_DEPTH,
    FASTENER_SLOT_DEPTH,
    FASTENER_SLOT_LENGTH,
    FASTENER_SLOT_WIDTH,
    FASTENER_STEM_RADIUS,
    FASTENER_TOP_RECESS,
    _seat_tool_local,
    _slotted_head_local,
    _oriented,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "reviews" / "R18_layout_manifest.json"
BASELINE_STEP = ROOT / "STEP" / "halberd_r18_layout_base.step"
APPROVED_BASE_HASH = "aa33330e16ed78918032a76e3374a82439a9d2445c5bca3d61c158ccb454fd21"
POCKET_DEPTH = 0.80
COVER_SETBACK = 0.18
PERIMETER_GAP = 0.30
FASTENER_REMAINING_WALL_MIN = 0.25
BODY_PAINT = "#A7B0B7"
METAL = "#87939B"


@dataclass
class AccessFeature:
    key: str
    host_label: str
    host_before: object
    host_after: object
    pocket_cutter: object
    seat_cutters: tuple
    slot_cutters: tuple
    parts: tuple
    screw_sites: tuple
    parameters: dict


def load_manifest():
    declare_input(MANIFEST_PATH)
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if data.get("base_document_hash") != APPROVED_BASE_HASH:
        raise ValueError("R18 layout manifest does not identify the approved saved base")
    return data


def load_saved_parts(step_path=BASELINE_STEP):
    scene = read_scene(step_path)
    leaves = tuple(scene.leaves())
    parts = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in leaves}
    if len(parts) != len(leaves):
        raise ValueError(f"{step_path.name}: duplicate saved leaf labels")
    return scene, parts


def _clock_frame(clock_degrees):
    angle = math.radians(clock_degrees)
    radial = bd.Vector(0.0, math.sin(angle), math.cos(angle))
    tangent = bd.Vector(0.0, math.cos(angle), -math.sin(angle))
    return radial, tangent


def radial_boundary(host, x, tangent_offset, clock_degrees, max_radius=260.0):
    """Measure the outer native skin on a fixed axial/tangential cross-section."""
    radial, tangent = _clock_frame(clock_degrees)
    inside = lambda radius: host.is_inside(
        bd.Vector(x, 0.0, 0.0) + tangent * tangent_offset + radial * radius)
    step = 0.5
    previous = None
    last_inside = None
    first_outer_exit = None
    radius = 0.0
    while radius <= max_radius:
        current = inside(radius)
        if current:
            last_inside = radius
        elif last_inside is not None:
            first_outer_exit = radius
        if first_outer_exit is not None:
            break
        previous = current
        radius += step
    if last_inside is None or first_outer_exit is None:
        raise ValueError(("no bounded native outer-skin crossing", x,
                          tangent_offset, clock_degrees, max_radius, previous))
    lo, hi = last_inside, first_outer_exit
    for _ in range(36):
        mid = (lo + hi) / 2.0
        if inside(mid):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _face_point_normal(face, target, outward):
    """Return the closest point on the trimmed native face and its normal."""
    surface_point, _target_point = face.closest_points(target)
    normal = face.normal_at(surface_point).normalized()
    if normal.dot(outward) < 0.0:
        normal = -normal
    return surface_point, normal, (surface_point - target).length


def measured_skin_point(host, x, tangent_offset, clock_degrees):
    """Resolve a manifest surface coordinate to a measured native face point."""
    radial, tangent = _clock_frame(clock_degrees)
    radius = radial_boundary(host, x, tangent_offset, clock_degrees)
    target = bd.Vector(x, 0.0, 0.0) + tangent * tangent_offset + radial * radius
    candidates = []
    for face in host.faces():
        box = face.bounding_box(optimal=False)
        if not (box.min.X - 0.5 <= target.X <= box.max.X + 0.5 and
                box.min.Y - 0.5 <= target.Y <= box.max.Y + 0.5 and
                box.min.Z - 0.5 <= target.Z <= box.max.Z + 0.5):
            continue
        point, normal, distance = _face_point_normal(face, target, radial)
        if distance > 0.35:
            continue
        if normal.dot(radial) < 0.25:
            continue
        candidates.append((distance, point, normal, face))
    if not candidates:
        raise ValueError(("manifest coordinate did not resolve to an outward native skin face",
                          x, tangent_offset, clock_degrees, tuple(target)))
    distance, point, normal, face = min(candidates, key=lambda row: row[0])
    if distance > 0.35:
        raise ValueError(("native-skin projection exceeds placement tolerance", distance,
                          x, tangent_offset, clock_degrees))
    return {
        "point": point,
        "normal": normal,
        "face": face,
        "ray_point": target,
        "projection_error_mm": distance,
        "measured_radius_mm": radius,
    }


def available_wall(host, point, outward, max_depth=400.0):
    from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
    from OCP.gce import gce_MakeLin

    point = bd.Vector(point)
    outward = bd.Vector(outward).normalized()
    inside = lambda depth: host.is_inside(point - outward * depth)
    if not inside(0.01):
        raise ValueError(("measured native skin point lacks host backing", tuple(point)))
    axis = bd.Axis(point, -outward)
    line = gce_MakeLin(axis.wrapped).Value()
    intersections = BRepIntCurveSurface_Inter()
    intersections.Init(host.wrapped, line, 1e-4)
    depths = []
    while intersections.More():
        hit = bd.Vector(intersections.Pnt())
        depth = (hit - point).dot(-outward)
        if 0.01 < depth <= max_depth:
            depths.append(depth)
        intersections.Next()

    distinct_depths = []
    for depth in sorted(depths):
        if not distinct_depths or depth - distinct_depths[-1] > 1e-5:
            distinct_depths.append(depth)
    previous = 0.01
    for index, depth in enumerate(distinct_depths):
        next_depth = distinct_depths[index + 1] if index + 1 < len(distinct_depths) \
            else max_depth
        if next_depth <= depth:
            continue
        after_depth = (depth + next_depth) / 2.0
        if not inside(after_depth):
            return depth
        previous = depth
    if inside(max_depth):
        raise ValueError(("native host support exceeds wall-probe bound",
                          tuple(point), max_depth))
    raise ValueError(("native ray reached exterior without a detected exit intersection",
                      tuple(point), previous, max_depth, distinct_depths))


def polygon_face(points):
    return bd.Face(bd.Wire.make_polygon(points))


def profile_prism(face, origin, outward, tangent, *, z_min=-40.0, z_max=40.0):
    """Make a local-profile mask aligned to body X, face tangent and radial axis."""
    local_face = face.moved(bd.Location((0.0, 0.0, z_min)))
    local_solid = bd.Solid.extrude(local_face, bd.Vector(0.0, 0.0, z_max - z_min))
    plane = bd.Plane(origin=origin, x_dir=(1.0, 0.0, 0.0), z_dir=outward)
    return local_solid.moved(plane.location)


def _union_shapes(shapes):
    if not shapes:
        raise ValueError("Cannot fuse an empty shape list")
    result = shapes[0]
    for shape in shapes[1:]:
        result = result + shape
    return result


def _native_skin_patches(faces, mask, outward):
    patches = []
    for face in faces:
        clipped = face & mask
        for patch in clipped.faces():
            if patch.area > 1e-6 and patch.normal_at().normalized().dot(outward) >= 0.25:
                patches.append(patch)
    if not patches:
        raise ValueError("F02 footprint did not clip any outward native skin patches")
    return tuple(patches)


def _extruded_skin_shell(patches, host, outward, offset, thickness, label):
    sections = []
    for patch in patches:
        start = patch.moved(bd.Location(-outward * offset)) if offset else patch
        section = bd.Solid.extrude(start, -outward * thickness)
        section = section & host
        if not section or section.volume <= 0.0 or not section.is_valid:
            raise ValueError((label, "native skin extrusion missed or invalidated host", patch.area))
        sections.append(section)
    shell = _union_shapes(sections)
    if not shell.is_valid or len(shell.solids()) != 1:
        raise ValueError((label, "native skin patches did not form one solid",
                          len(shell.solids())))
    return shell


def _slotted_hardware(host, host_label, feature_id, center_x, center_tangent,
                     clock, screw_coordinates):
    local_seat = _seat_tool_local()
    local_head, local_slot = _slotted_head_local()
    radial, tangent = _clock_frame(clock)
    seats, slots, heads, sites = [], [], [], []
    for index, (offset_x, offset_tangent) in enumerate(screw_coordinates, 1):
        surface = measured_skin_point(host, center_x + offset_x,
                                      center_tangent + offset_tangent, clock)
        point, normal = surface["point"], surface["normal"]
        wall = available_wall(host, point, normal)
        remaining = wall - FASTENER_SEAT_DEPTH
        if remaining <= FASTENER_REMAINING_WALL_MIN:
            raise ValueError((feature_id, index, wall, remaining,
                              "standard R17 short fastener has insufficient backing"))
        x_direction = bd.Vector(1.0, 0.0, 0.0) - normal * normal.dot(
            bd.Vector(1.0, 0.0, 0.0))
        if x_direction.length < 1e-6:
            x_direction = tangent
        seat, _ = _oriented(local_seat, point, normal, x_direction)
        head, _ = _oriented(local_head, point, normal, x_direction)
        slot, _ = _oriented(local_slot, point, normal, x_direction)
        seat.label = f"r18_{feature_id}_seat_{index}"
        head.label = f"r18_{feature_id}_fastener_{index}"
        head.color = srgb(METAL)
        slot.label = f"r18_{feature_id}_slot_{index}"
        seats.append(seat)
        slots.append(slot)
        heads.append(head)
        sites.append({
            "offset_x_mm": float(offset_x),
            "offset_tangent_mm": float(offset_tangent),
            "point_mm": [point.X, point.Y, point.Z],
            "ray_point_mm": [surface["ray_point"].X,
                             surface["ray_point"].Y,
                             surface["ray_point"].Z],
            "outward_normal": [normal.X, normal.Y, normal.Z],
            "projection_error_mm": surface["projection_error_mm"],
            "measured_skin_radius_mm": surface["measured_radius_mm"],
            "available_wall_mm": wall,
            "remaining_wall_after_seat_mm": remaining,
            "seat_depth_mm": FASTENER_SEAT_DEPTH,
            "head_top_recess_mm": FASTENER_TOP_RECESS,
            "countersink_top_radius_mm": FASTENER_COUNTERSINK_TOP_RADIUS,
        })
    return tuple(seats), tuple(slots), tuple(heads), tuple(sites)


def build_f02_native_preflight(host, manifest=None):
    """Build and measure only the uncertain conformal F02 shoulder hatch."""
    data = manifest or load_manifest()
    feature = next(item for item in data["individual_access_features"]
                   if item["id"] == "F02")
    if (feature["face"], feature["clock"], feature["x"], feature["tangent"]) != \
            ("upper", 0, 900.0, 0.0):
        raise ValueError("The approved F02 layout placement changed; primary review required")
    if len(host.solids()) != 1 or not host.is_valid:
        raise ValueError("F02 host must be one valid saved R18 native solid")

    radial, tangent = _clock_frame(feature["clock"])
    center_radius = radial_boundary(host, feature["x"], feature["tangent"],
                                    feature["clock"])
    center = (bd.Vector(feature["x"], 0.0, 0.0) +
              tangent * feature["tangent"] + radial * center_radius)
    outline = polygon_face(feature["outline"])
    mask = profile_prism(outline, center, radial, tangent)
    cover_face = bd.Wire.make_polygon(feature["outline"]).offset_2d(-PERIMETER_GAP)
    inset_mask = profile_prism(bd.Face(cover_face), center, radial, tangent)

    # Resolve the footprint against measured native points, then trim those
    # actual skin faces to the approved planform. Extrusion preserves their
    # curved surface while producing the exact translated .8 mm shell locally.
    skin_samples = []
    skin_faces = []
    for dx in (-62.0, 0.0, 60.0):
        for dy in (-16.0, 0.0, 16.0):
            surface = measured_skin_point(host, feature["x"] + dx,
                                          feature["tangent"] + dy,
                                          feature["clock"])
            point, normal = surface["point"], surface["normal"]
            skin_samples.append({
                "offset_mm": [dx, dy],
                "point_mm": [point.X, point.Y, point.Z],
                "ray_point_mm": [surface["ray_point"].X,
                                  surface["ray_point"].Y,
                                  surface["ray_point"].Z],
                "radius_mm": surface["measured_radius_mm"],
                "projection_error_mm": surface["projection_error_mm"],
                "outward_normal": [normal.X, normal.Y, normal.Z],
                "backed_wall_mm": available_wall(host, point, normal),
            })
            face = surface["face"]
            if not any(face.is_same(existing) for existing in skin_faces):
                skin_faces.append(face)

    pocket_patches = _native_skin_patches(skin_faces, mask, radial)
    pocket = _extruded_skin_shell(pocket_patches, host, radial, 0.0,
                                  POCKET_DEPTH, "F02 pocket")
    if not pocket or pocket.volume <= 0.0 or not pocket.is_valid:
        raise ValueError("F02 native shoulder shell/outline intersection is empty or invalid")

    seats, slots, heads, sites = _slotted_hardware(
        host, "main_body_intake_r12", "F02", feature["x"],
        feature["tangent"], feature["clock"], feature["screws"])
    host_after = host - pocket
    for seat in seats:
        host_after = host_after - seat
    host_after.label = "main_body_intake_r12_r18_access_cut"
    host_after.color = host.color

    cover_patches = _native_skin_patches(skin_faces, inset_mask, radial)
    cover = _extruded_skin_shell(cover_patches, host, radial, COVER_SETBACK,
                                 POCKET_DEPTH - COVER_SETBACK, "F02 cover")
    for seat in seats:
        cover = cover - seat
    cover.label = "r18_F02_cover"
    cover.color = host.color

    return AccessFeature(
        key="F02", host_label="main_body_intake_r12", host_before=host,
        host_after=host_after, pocket_cutter=pocket, seat_cutters=seats,
        slot_cutters=slots, parts=(cover, *heads), screw_sites=sites,
        parameters={
            "face": feature["face"],
            "clock_degrees": feature["clock"],
            "center_x_mm": feature["x"],
            "center_tangent_mm": feature["tangent"],
            "outline_local_mm": feature["outline"],
            "pocket_depth_mm": POCKET_DEPTH,
            "cover_setback_mm": COVER_SETBACK,
            "perimeter_gap_mm": PERIMETER_GAP,
            "skin_center_radius_mm": center_radius,
            "pocket_volume_mm3": pocket.volume,
            "pocket_bounds_mm": [pocket.bounding_box().min.X,
                                  pocket.bounding_box().min.Y,
                                  pocket.bounding_box().min.Z,
                                  pocket.bounding_box().max.X,
                                  pocket.bounding_box().max.Y,
                                  pocket.bounding_box().max.Z],
            "skin_samples": skin_samples,
            "screw_sites": list(sites),
        })
