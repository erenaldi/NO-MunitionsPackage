"""R18 approved access-feature construction and deterministic preflight."""
from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from cadgen import build123d as bd, srgb

from halberd_r17_interface_shapes import (
    FASTENER_SEAT_DEPTH,
    FASTENER_TOP_RECESS,
    _oriented,
    _seat_tool_local,
    _slotted_head_local,
    nozzle_lip_interface,
)
from halberd_r18_access_shapes import (
    APPROVED_BASE_HASH,
    BASELINE_STEP,
    BODY_PAINT,
    COVER_SETBACK,
    FASTENER_REMAINING_WALL_MIN,
    METAL,
    PERIMETER_GAP,
    POCKET_DEPTH,
    _extruded_skin_shell,
    _native_skin_patches,
    _slotted_hardware,
    _union_shapes,
    available_wall,
    build_f02_native_preflight,
    load_manifest,
    load_saved_parts,
    measured_skin_point,
    profile_prism,
)
from halberd_r18_layout_base import MATERIALS as R18_BASE_MATERIALS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_METADATA = ROOT / "reviews" / "halberd_r18_access_layout.json"
MAIN_HOST = "main_body_intake_r12"
BOOSTER_HOST = "booster_body"
NOZZLE_PARAMETERS = {
    "main_nozzle": {
        "mouth_x": -1123.3333333333,
        "cavity_radius": 65.0,
        "outer_limit_radius": 100.0,
        "ring_cut_radii": (70.0, 73.0),
        "ring_insert_radii": (70.25, 72.75),
        "screw_radius": 91.5,
    },
    "booster_nozzle": {
        "mouth_x": -1685.0,
        "cavity_radius": 69.0,
        "outer_limit_radius": 82.0,
        "ring_cut_radii": (70.0, 73.0),
        "ring_insert_radii": (70.25, 72.75),
        "screw_radius": 78.4,
    },
}
CROP_BOUNDS = {
    "F02": (805.0, 995.0),
    "forward_F04A_F03A": (330.0, 630.0),
    "F04B": (-890.0, -690.0),
    "F05": (-145.0, 425.0),
    "booster_F10_F03B": (-1530.0, -1320.0),
}


@dataclass
class R18Build:
    scene: object
    baseline_parts: dict
    component_map: dict
    per_host_cutters: dict
    new_parts: dict
    owner_map: dict
    family_map: dict
    feature_map: dict
    seat_slot_data: dict
    actual_parameters: dict
    compound: object


def _circle_wire(radius, center=(0.0, 0.0)):
    return bd.Wire.make_circle(radius).moved(bd.Location((center[0], center[1], 0.0)))


def _circle_face(radius, center=(0.0, 0.0)):
    return bd.Face(_circle_wire(radius, center))


def _polygon_wire(points):
    return bd.Wire.make_polygon([(float(x), float(y), 0.0) for x, y in points], close=True)


def _d_door_wire():
    a = (-45.0, -20.0, 0.0)
    b = (65.0, -20.0, 0.0)
    c = (65.0, 20.0, 0.0)
    d = (-45.0, 20.0, 0.0)
    return bd.Wire([
        bd.Edge.make_line(a, b),
        bd.Edge.make_line(b, c),
        bd.Edge.make_line(c, d),
        bd.Edge.make_three_point_arc(d, (-65.0, 0.0, 0.0), a),
    ])


def _keyed_cap_wire():
    flat_x = 7.8
    radius = 12.0
    half_chord = math.sqrt(radius * radius - flat_x * flat_x)
    upper = (flat_x, half_chord, 0.0)
    lower = (flat_x, -half_chord, 0.0)
    return bd.Wire([
        bd.Edge.make_three_point_arc(upper, (-radius, 0.0, 0.0), lower),
        bd.Edge.make_line(lower, upper),
    ])


def _clip_half_plane(face, point, direction, keep_sign, margin=0.0):
    """Clip a local planar face to one side of a line with a signed inset."""
    px, py = point
    dx, dy = direction
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        raise ValueError("Invalid R18 split line")
    xmin, ymin, xmax, ymax = -1000.0, -1000.0, 1000.0, 1000.0
    polygon = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]

    def signed(p):
        return keep_sign * (dx * (p[1] - py) - dy * (p[0] - px)) / length - margin

    clipped = []
    previous = polygon[-1]
    previous_value = signed(previous)
    for current in polygon:
        current_value = signed(current)
        previous_inside = previous_value >= -1e-9
        current_inside = current_value >= -1e-9
        if previous_inside != current_inside:
            ratio = previous_value / (previous_value - current_value)
            clipped.append((previous[0] + ratio * (current[0] - previous[0]),
                            previous[1] + ratio * (current[1] - previous[1])))
        if current_inside:
            clipped.append(current)
        previous, previous_value = current, current_value
    if len(clipped) < 3:
        raise ValueError("R18 split region is empty")
    region = bd.Face(_polygon_wire(clipped))
    result = face & region
    if not result or result.area <= 1e-6:
        raise ValueError("R18 split produced an empty cover section")
    return result


def _f05_cover_sections(feature):
    inset_wire = _polygon_wire(feature["outline"]).offset_2d(-PERIMETER_GAP)
    inset = bd.Face(inset_wire)
    left = _clip_half_plane(inset, (-237.0, 0.0), (0.0, 1.0), +1, 0.15)
    center = _clip_half_plane(inset, (-237.0, 0.0), (0.0, 1.0), -1, 0.15)
    split_point = (225.0, -8.0)
    split_direction = (12.0, 13.0)
    center = _clip_half_plane(center, split_point, split_direction, +1, 0.15)
    right = _clip_half_plane(inset, split_point, split_direction, -1, 0.15)
    return (("terminal_left", left), ("center_strip", center), ("terminal_right", right))


def _feature_profile(feature):
    feature_id = feature["id"]
    if feature_id == "F04B":
        return bd.Face(_d_door_wire())
    if feature_id == "F03A":
        return _circle_face(18.0)
    if feature_id == "F03B":
        return bd.Face(_keyed_cap_wire())
    if feature_id == "F05":
        return bd.Face(_polygon_wire(feature["outline"]))
    return bd.Face(_polygon_wire(feature["outline"]))


def _feature_wire(feature):
    feature_id = feature["id"]
    if feature_id == "F04B":
        return _d_door_wire()
    if feature_id == "F03A":
        return _circle_wire(18.0)
    if feature_id == "F03B":
        return _keyed_cap_wire()
    return _polygon_wire(feature["outline"])


def _cover_profiles(feature):
    feature_id = feature["id"]
    if feature_id == "F03A":
        ring = _circle_face(17.7) - _circle_face(15.5)
        disc = _circle_face(15.2)
        return (("ring", ring, "retaining_ring"),
                ("disc", disc, "body_tone_cover"))
    if feature_id == "F05":
        return tuple((key, face, "terminal_piece" if key.startswith("terminal")
                      else "body_tone_cover")
                     for key, face in _f05_cover_sections(feature))
    pocket_wire = _feature_wire(feature)
    inset_wire = pocket_wire.offset_2d(-PERIMETER_GAP)
    if feature_id == "F04B":
        return (("cover", bd.Face(inset_wire), "body_tone_cover"),)
    if feature_id == "F03B":
        return (("keyed_cap", bd.Face(inset_wire), "body_tone_cover"),)
    return (("cover", bd.Face(inset_wire), "body_tone_cover"),)


def _sample_outline(feature):
    feature_id = feature["id"]
    if feature_id == "F03A":
        return [(18.0 * math.cos(2.0 * math.pi * index / 24.0),
                 18.0 * math.sin(2.0 * math.pi * index / 24.0))
                for index in range(24)]
    if feature_id == "F03B":
        radius, flat_x = 12.0, 7.8
        start = math.acos(flat_x / radius)
        end = 2.0 * math.pi - start
        arc = [(radius * math.cos(start + (end - start) * index / 24.0),
                radius * math.sin(start + (end - start) * index / 24.0))
               for index in range(25)]
        return arc + [(flat_x, 0.0)]
    if feature_id == "F04B":
        return [(-45, -20), (65, -20), (65, 20), (-45, 20),
                (-59.1421356, 14.1421356), (-65, 0), (-59.1421356, -14.1421356)]
    if feature_id == "F05":
        return list(feature["outline"]) + [(-125, 0), (125, 0)]
    return list(feature["outline"])


def _collect_skin(host, feature):
    radial_clock = math.radians(feature["clock"])
    radial = bd.Vector(0.0, math.sin(radial_clock), math.cos(radial_clock))
    tangent = bd.Vector(0.0, math.cos(radial_clock), -math.sin(radial_clock))
    center = measured_skin_point(host, feature["x"], feature["tangent"], feature["clock"])
    center_point = center["point"]
    center_normal = center["normal"].normalized()
    if center_normal.dot(radial) < 0.90:
        raise ValueError((feature["id"], "native face normal materially departs from the approved clock frame",
                          center_normal.dot(radial)))
    faces = [center["face"]]
    samples = []
    local_samples = list(_sample_outline(feature))
    local_samples.extend(tuple(site) for site in feature.get("screws", ()))
    for dx, dy in local_samples:
        surface = measured_skin_point(host, feature["x"] + dx,
                                      feature["tangent"] + dy,
                                      feature["clock"])
        point, normal = surface["point"], surface["normal"]
        if normal.dot(center_normal) < 0.985:
            raise ValueError((feature["id"], "flat-face support varies too much for the approved seat",
                              dx, dy, normal.dot(center_normal)))
        if not any(surface["face"].is_same(face) for face in faces):
            faces.append(surface["face"])
        samples.append({
            "offset_mm": [float(dx), float(dy)],
            "point_mm": [point.X, point.Y, point.Z],
            "outward_normal": [normal.X, normal.Y, normal.Z],
            "projection_error_mm": surface["projection_error_mm"],
            "measured_skin_radius_mm": surface["measured_radius_mm"],
            "available_wall_mm": available_wall(host, point, normal),
        })
    return center, center_point, center_normal, tangent, tuple(faces), samples


def _set_label_color(shape, label, color=None):
    shape.label = label
    if color is not None:
        shape.color = srgb(color)
    return shape


def _validate_cut(owner, before, after, cutters, owner_label):
    if not after or not after.is_valid or len(after.solids()) != 1:
        raise ValueError((owner_label, "cut owner is empty, invalid, or split into multiple solids"))
    if after.volume >= before.volume - 1e-7:
        raise ValueError((owner_label, "declared pocket/seat cutters did not remove host volume",
                          before.volume, after.volume))
    for cutter in cutters:
        if not cutter or not cutter.is_valid or cutter.volume <= 1e-7:
            raise ValueError((owner_label, "invalid or empty saved-host cutter", cutter.label))


def _build_planar_feature(host, host_label, feature, stage):
    feature_id = feature["id"]
    center, origin, outward, tangent, native_faces, skin_samples = _collect_skin(host, feature)
    profile = _feature_profile(feature)
    mask = profile_prism(profile, origin, outward, tangent)
    pocket_patches = _native_skin_patches(native_faces, mask, outward)
    patch_area = sum(patch.area for patch in pocket_patches)
    if patch_area < profile.area * 0.995:
        raise ValueError((feature_id, "native host clips away part of the approved outline",
                          profile.area, patch_area))
    pocket = _extruded_skin_shell(pocket_patches, host, outward, 0.0,
                                  POCKET_DEPTH, f"{stage}_r18_{feature_id}_pocket")

    seats, slots, heads, screw_sites = _slotted_hardware(
        host, host_label, feature_id, feature["x"], feature["tangent"],
        feature["clock"], feature.get("screws", ()))
    before = host
    after = host - pocket
    for seat in seats:
        after = after - seat
    after.label = host_label
    after.color = host.color
    cutters = (pocket, *seats)
    _validate_cut(host_label, before, after, cutters, host_label)

    created = []
    families = {}
    cover_data = []
    for suffix, cover_profile, family in _cover_profiles(feature):
        cover_mask = profile_prism(cover_profile, origin, outward, tangent)
        cover_patches = _native_skin_patches(native_faces, cover_mask, outward)
        cover = _extruded_skin_shell(cover_patches, host, outward, COVER_SETBACK,
                                     POCKET_DEPTH - COVER_SETBACK,
                                     f"{stage}_r18_{feature_id}_{suffix}")
        for seat in seats:
            cover = cover - seat
        if not cover or not cover.is_valid or len(cover.solids()) != 1:
            raise ValueError((feature_id, suffix, "cover is empty, invalid, or not one solid"))
        if family == "terminal_piece":
            part_label = f"{stage}_r18_F05_{suffix}"
            _set_label_color(cover, part_label, METAL)
        elif feature_id == "F03A" and suffix == "ring":
            part_label = f"{stage}_r18_F03A_ring"
            _set_label_color(cover, part_label, METAL)
        elif feature_id == "F03A" and suffix == "disc":
            part_label = f"{stage}_r18_F03A_disc"
            _set_label_color(cover, part_label, BODY_PAINT)
        elif feature_id == "F03B":
            part_label = f"{stage}_r18_F03B_keyed_cap"
            _set_label_color(cover, part_label, BODY_PAINT)
        else:
            part_label = f"{stage}_r18_{feature_id}_cover"
            _set_label_color(cover, part_label, BODY_PAINT)
        created.append(cover)
        families[part_label] = family
        cover_data.append({"label": part_label, "profile_area_mm2": cover_profile.area,
                           "native_patch_area_mm2": sum(p.area for p in cover_patches)})

    for index, head in enumerate(heads, 1):
        label = f"{stage}_r18_{feature_id}_fastener_{index}"
        _set_label_color(head, label, METAL)
        created.append(head)
        families[label] = "slotted_fastener"

    slot_data = {
        "screw_sites": list(screw_sites),
        "slot_cutters": [slot.label for slot in slots],
    }
    if feature_id == "F03B":
        slot_center_x = -0.5  # exact midpoint of the manifest's [-6, +5] line
        slot_center = origin + bd.Vector(1.0, 0.0, 0.0) * slot_center_x \
            - outward * (COVER_SETBACK + 0.25)
        slot_plane = bd.Plane(origin=slot_center, x_dir=(1.0, 0.0, 0.0), z_dir=outward)
        shallow_slot = bd.Box(11.0, 0.8, 0.502).moved(slot_plane.location)
        cap_index = next(index for index, part in enumerate(created)
                         if part.label == f"{stage}_r18_F03B_keyed_cap")
        keyed_cap = created[cap_index] - shallow_slot
        if not keyed_cap or not keyed_cap.is_valid or len(keyed_cap.solids()) != 1:
            raise ValueError("F03B shallow central slot invalidated the keyed cap")
        keyed_cap.label = f"{stage}_r18_F03B_keyed_cap"
        keyed_cap.color = srgb(BODY_PAINT)
        created[cap_index] = keyed_cap
        shallow_slot.label = f"{stage}_r18_F03B_shallow_slot_cutter"
        slot_data["keyed_slot"] = {
            "center_local_mm": [slot_center_x, 0.0],
            "length_mm": 11.0,
            "width_mm": 0.8,
            "depth_mm": 0.50,
            "cutter_label": shallow_slot.label,
        }

    cutters[0].label = f"{stage}_r18_{feature_id}_pocket"
    for index, cutter in enumerate(cutters[1:], 1):
        cutter.label = f"{stage}_r18_{feature_id}_seat_{index}"
    for index, cutter in enumerate(slots, 1):
        cutter.label = f"{stage}_r18_{feature_id}_fastener_slot_{index}"
    feature_map = [part.label for part in created]
    parameters = {
        "face": feature["face"],
        "clock_degrees": feature["clock"],
        "center_x_mm": feature["x"],
        "center_tangent_mm": feature["tangent"],
        "manifest_outline_local_mm": feature["outline"],
        "screw_coordinates_local_mm": feature.get("screws", []),
        "pocket_depth_mm": POCKET_DEPTH,
        "cover_setback_mm": COVER_SETBACK,
        "perimeter_gap_mm": PERIMETER_GAP,
        "pocket_volume_mm3": pocket.volume,
        "native_skin_samples": skin_samples,
        "cover_profiles": cover_data,
        "screw_sites": list(screw_sites),
        "patch_area_mm2": patch_area,
    }
    return after, cutters, created, families, feature_map, slot_data, parameters


def _build_nozzle(host, stage):
    host_label = MAIN_HOST if stage == "main" else BOOSTER_HOST
    key = f"{stage}_nozzle"
    params = dict(NOZZLE_PARAMETERS[key])
    proto = nozzle_lip_interface(
        host, host_label, key=key,
        mouth_x=params["mouth_x"], cavity_radius=params["cavity_radius"],
        outer_limit_radius=params["outer_limit_radius"],
        ring_cut_radii=params["ring_cut_radii"],
        ring_insert_radii=params["ring_insert_radii"],
        screw_radius=params["screw_radius"],
    )
    proto.host_after.label = host_label
    proto.host_after.color = host.color
    _validate_cut(host_label, host, proto.host_after, proto.cutters, host_label)
    for index, part in enumerate(proto.parts):
        label = f"{stage}_r18_nozzle_ring" if index == 0 else \
            f"{stage}_r18_nozzle_fastener_{index}"
        _set_label_color(part, label, METAL)
    proto.cutters[0].label = f"{stage}_r18_nozzle_annular_seat"
    for index, cutter in enumerate(proto.cutters[1:], 1):
        cutter.label = f"{stage}_r18_nozzle_fastener_seat_{index}"
    for index, cutter in enumerate(proto.slot_cutters, 1):
        cutter.label = f"{stage}_r18_nozzle_fastener_slot_{index}"
    sites = []
    for row in proto.parameters["screw_sites"]:
        point = bd.Vector(*row["center_mm"])
        # Nozzle fasteners face axially into the stage; unlike radial hatch
        # seats, their backing path spans much of the 3.37 m airframe.
        wall = available_wall(host, point, (-1.0, 0.0, 0.0), max_depth=4000.0)
        remaining = wall - FASTENER_SEAT_DEPTH
        if remaining <= FASTENER_REMAINING_WALL_MIN:
            raise ValueError((key, row["clock_degrees"], wall, remaining,
                              "nozzle rim fastener seat lacks saved-host backing"))
        site = dict(row)
        site["available_wall_mm"] = wall
        site["remaining_wall_after_seat_mm"] = remaining
        sites.append(site)
    proto.parameters["screw_sites"] = sites
    params["ring_recess_depth_mm"] = proto.parameters["ring_recess_depth_mm"]
    params["ring_inset_mm"] = proto.parameters["ring_inset_mm"]
    params["screw_sites"] = sites
    return proto.host_after, tuple(proto.cutters), list(proto.parts), params, \
        tuple(cutter.label for cutter in proto.slot_cutters)


def _bbox_overlaps(first, second, tolerance=1e-5):
    a, b = first.bounding_box(), second.bounding_box()
    return (a.min.X <= b.max.X + tolerance and a.max.X >= b.min.X - tolerance and
            a.min.Y <= b.max.Y + tolerance and a.max.Y >= b.min.Y - tolerance and
            a.min.Z <= b.max.Z + tolerance and a.max.Z >= b.min.Z - tolerance)


def _intersection_volume(first, second):
    if not _bbox_overlaps(first, second):
        return 0.0
    common = first & second
    return common.volume if common else 0.0


def _check_no_detail_overlap(component_map, baseline_parts, new_parts, owner_map):
    for label, detail in new_parts.items():
        owner = owner_map[label]
        overlap = _intersection_volume(component_map[owner], detail)
        if overlap > 1e-5:
            raise ValueError((label, owner, "detail overlaps its cut owner", overlap))
        for baseline_label, baseline_part in baseline_parts.items():
            if baseline_label == owner:
                continue
            overlap = _intersection_volume(baseline_part, detail)
            if overlap > 1e-5:
                raise ValueError((label, baseline_label,
                                  "detail overlaps a retained baseline component", overlap))
    labels = list(new_parts)
    for left_index, left_label in enumerate(labels):
        for right_label in labels[left_index + 1:]:
            if owner_map[left_label] == owner_map[right_label] and \
                    _intersection_volume(new_parts[left_label], new_parts[right_label]) > 1e-5:
                raise ValueError((left_label, right_label, "new details overlap each other"))


def _serialize_bounds(shape):
    box = shape.bounding_box()
    return [box.min.X, box.min.Y, box.min.Z, box.max.X, box.max.Y, box.max.Z]


def _planned_crop_labels(feature_map):
    return {
        "F02": [MAIN_HOST, *feature_map["F02"]],
        "forward_F04A_F03A": [MAIN_HOST, *feature_map["F04A"], *feature_map["F03A"]],
        "F04B": [MAIN_HOST, *feature_map["F04B"]],
        "F05": [MAIN_HOST, *feature_map["F05"]],
        "booster_F10_F03B": [BOOSTER_HOST, *feature_map["F10"], *feature_map["F03B"]],
    }


def _write_metadata(result, baseline_scene):
    source_files = [Path(__file__),
                    Path(__file__).with_name("halberd_r18_access_shapes.py"),
                    Path(__file__).with_name("halberd_r18_access.py")]
    metadata = {
        "gate": "R18 gate2 source+build",
        "source_hashes_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in source_files},
        "baseline_step": str(BASELINE_STEP),
        "baseline_document_hash": baseline_scene.document_hash,
        "approved_baseline_hash": APPROVED_BASE_HASH,
        "manifest_path": str(ROOT / "reviews" / "R18_layout_manifest.json"),
        "baseline_part_count": len(result.baseline_parts),
        "access_feature_count": len(result.feature_map),
        "access_part_count": sum(len(labels) for labels in result.feature_map.values()),
        "nozzle_part_count": sum(1 for label in result.new_parts
                                  if "_r18_nozzle_" in label and "fastener" in label or
                                  "_r18_nozzle_ring" in label),
        "full_part_count": len(result.component_map) + len(result.new_parts),
        "baseline_component_map": {
            label: {"output_label": result.component_map[label].label,
                    "owner": label}
            for label in result.baseline_parts
        },
        "per_host_cutters": {
            owner: [{"label": cutter.label, "volume_mm3": cutter.volume,
                     "bounds_mm": _serialize_bounds(cutter)}
                    for cutter in cutters]
            for owner, cutters in result.per_host_cutters.items()
        },
        "new_parts": list(result.new_parts),
        "owner_map": result.owner_map,
        "family_map": result.family_map,
        "feature_map": result.feature_map,
        "seat_slot_data": result.seat_slot_data,
        "actual_parameters": result.actual_parameters,
        "review_crops": {
            key: {"axial_bounds_mm": list(bounds),
                  "selected_labels": metadata_crop_labels(key)}
            for key, bounds in CROP_BOUNDS.items()
        },
        "preflight": {
            "all_new_parts_valid_single_solids": all(
                part.is_valid and len(part.solids()) == 1
                for part in result.new_parts.values()),
            "all_final_baseline_parts_valid_single_solids": all(
                part.is_valid and len(part.solids()) == 1
                for part in result.component_map.values()),
            "owner_and_detail_overlap_mm3_max": 0.0,
            "host_gain": False,
            "saved_geometry_checks_deferred_to_next_gate": True,
        },
    }
    OUTPUT_METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def build_r18_access():
    """Build and preflight the seven approved access details and R17 nozzle rims."""
    manifest = load_manifest()
    scene, baseline = load_saved_parts(BASELINE_STEP)
    if scene.document_hash != APPROVED_BASE_HASH:
        raise ValueError("R18 access build requires the exact approved 28-part planning base")
    if len(baseline) != 28 or MAIN_HOST not in baseline or BOOSTER_HOST not in baseline:
        raise ValueError(f"R18 planning base composition mismatch: {len(baseline)} leaves")

    component_map = dict(baseline)
    per_host_cutters = {MAIN_HOST: [], BOOSTER_HOST: []}
    new_parts = {}
    owner_map = {}
    family_map = {}
    feature_map = {}
    seat_slot_data = {}
    actual_parameters = {}
    feature_by_id = {item["id"]: item for item in manifest["individual_access_features"]}
    if set(feature_by_id) != {"F02", "F04A", "F04B", "F05", "F03A", "F03B", "F10"}:
        raise ValueError("R18 manifest access feature IDs changed from the seven approved designs")
    stage_by_feature = {
        "F02": ("main", MAIN_HOST), "F04A": ("main", MAIN_HOST),
        "F04B": ("main", MAIN_HOST), "F05": ("main", MAIN_HOST),
        "F03A": ("main", MAIN_HOST), "F03B": ("booster", BOOSTER_HOST),
        "F10": ("booster", BOOSTER_HOST),
    }

    for feature_id in ("F02", "F04A", "F04B", "F05", "F03A", "F03B", "F10"):
        feature = feature_by_id[feature_id]
        stage, host_label = stage_by_feature[feature_id]
        host = component_map[host_label]
        if feature_id == "F02":
            proto = build_f02_native_preflight(host, manifest)
            after = proto.host_after
            after.label = host_label
            after.color = host.color
            cutters = (proto.pocket_cutter, *proto.seat_cutters)
            cutters[0].label = "main_r18_F02_pocket"
            for index, cutter in enumerate(cutters[1:], 1):
                cutter.label = f"main_r18_F02_seat_{index}"
            for index, cutter in enumerate(proto.slot_cutters, 1):
                cutter.label = f"main_r18_F02_fastener_slot_{index}"
            details = list(proto.parts)
            for index, detail in enumerate(details):
                suffix = "cover" if index == 0 else f"fastener_{index}"
                _set_label_color(detail, f"main_r18_F02_{suffix}", BODY_PAINT if index == 0 else METAL)
            families = {part.label: ("body_tone_cover" if "_cover" in part.label
                                     else "slotted_fastener") for part in details}
            _validate_cut(host_label, host, after, cutters, host_label)
            feature_map[feature_id] = [part.label for part in details]
            screw_data = {"screw_sites": list(proto.screw_sites),
                          "slot_cutters": [slot.label for slot in proto.slot_cutters]}
            parameters = dict(proto.parameters)
            parameters["screw_sites"] = list(proto.screw_sites)
            actual_parameters[feature_id] = parameters
        else:
            after, cutters, details, families, labels, screw_data, parameters = \
                _build_planar_feature(host, host_label, feature, stage)
            feature_map[feature_id] = labels
            actual_parameters[feature_id] = parameters
        component_map[host_label] = after
        per_host_cutters[host_label].extend(cutters)
        new_parts.update({part.label: part for part in details})
        owner_map.update({part.label: host_label for part in details})
        family_map.update(families)
        seat_slot_data[feature_id] = screw_data

    for nozzle_key, (stage, host_label) in {
        "main_nozzle": ("main", MAIN_HOST),
        "booster_nozzle": ("booster", BOOSTER_HOST),
    }.items():
        before = component_map[host_label]
        after, cutters, details, params, nozzle_slots = _build_nozzle(before, stage)
        component_map[host_label] = after
        per_host_cutters[host_label].extend(cutters)
        new_parts.update({part.label: part for part in details})
        owner_map.update({part.label: host_label for part in details})
        family_map.update({part.label: ("nozzle_retaining_ring" if part.label.endswith("_ring")
                                        else "slotted_fastener") for part in details})
        seat_slot_data[nozzle_key] = {"screw_sites": params["screw_sites"],
                                      "slot_cutters": list(nozzle_slots)}
        actual_parameters[nozzle_key] = params

    if len(feature_map) != 7 or sum(len(labels) for labels in feature_map.values()) != 31:
        raise ValueError("R18 access part count does not match the seven distinct designs")
    if len(new_parts) != 49 or len(component_map) + len(new_parts) != 77:
        raise ValueError(("R18 full assembly part-count discrepancy",
                          len(component_map), len(new_parts)))
    all_labels = list(component_map) + list(new_parts)
    if len(all_labels) != len(set(all_labels)):
        raise ValueError("R18 output contains duplicate saved-part labels")
    for label, part in {**component_map, **new_parts}.items():
        if not part or not part.is_valid or len(part.solids()) != 1 or part.volume <= 1e-8:
            raise ValueError((label, "output part is empty, invalid, or not one positive solid"))
    _check_no_detail_overlap(component_map, baseline, new_parts, owner_map)

    actual_parameters["nozzle_r17_constants"] = {
        key: {name: list(value) if isinstance(value, tuple) else value
              for name, value in values.items()}
        for key, values in NOZZLE_PARAMETERS.items()
    }
    actual_parameters["construction_constants"] = {
        "pocket_depth_mm": POCKET_DEPTH,
        "cover_setback_mm": COVER_SETBACK,
        "perimeter_gap_mm": PERIMETER_GAP,
        "fastener_seat_depth_mm": FASTENER_SEAT_DEPTH,
        "fastener_top_recess_mm": FASTENER_TOP_RECESS,
    }
    compound_parts = [component_map[label] for label in baseline]
    compound_parts.extend(new_parts.values())
    compound = bd.Compound(children=compound_parts, label="Halberd_R18_Access")
    result = R18Build(
        scene=scene, baseline_parts=baseline, component_map=component_map,
        per_host_cutters={key: tuple(value) for key, value in per_host_cutters.items()},
        new_parts=new_parts, owner_map=owner_map, family_map=family_map,
        feature_map=feature_map, seat_slot_data=seat_slot_data,
        actual_parameters=actual_parameters, compound=compound,
    )
    _write_metadata(result, scene)
    return result


def materials_for_labels(labels, *, include_all_base=False):
    """Filter inherited base assignments and add only resolved detail labels."""
    selected = set(labels)
    materials = deepcopy(R18_BASE_MATERIALS)
    assignments = []
    for assignment in materials["assignments"]:
        if include_all_base:
            targets = list(assignment["targets"])
        else:
            targets = []
            for target in assignment["targets"]:
                source_label = target.lstrip("#")
                if source_label in selected:
                    targets.append(target)
                targets.extend(f"#{label}" for label in selected
                               if label.startswith(f"{source_label}_r18_crop_"))
        if targets:
            entry = deepcopy(assignment)
            entry["targets"] = targets
            assignments.append(entry)
    detail_targets = []
    metal_targets = []
    for label in selected:
        if label.endswith("_ring") or "terminal_" in label or "fastener_" in label:
            metal_targets.append(f"#{label}")
        elif "_r18_F03A_disc" in label or "_r18_F03B_keyed_cap" in label or \
                "_r18_" in label and ("_cover" in label or "_strip" in label):
            detail_targets.append(f"#{label}")
    if detail_targets:
        assignments.append({"targets": sorted(detail_targets), "material": "detail_paint"})
    if metal_targets:
        assignments.append({"targets": sorted(metal_targets), "material": "detail_metal"})
    materials["assignments"] = assignments
    return materials


def crop_access_variant(full_shape, variant):
    """Return one exact authorized crop and its saved-leaf labels/bounds."""
    bounds = CROP_BOUNDS[variant]
    by_label = {child.label: child for child in full_shape.children}
    feature_map = _planned_crop_labels({
        "F02": ["main_r18_F02_cover", *(f"main_r18_F02_fastener_{i}" for i in range(1, 5))],
        "F04A": ["main_r18_F04A_cover", *(f"main_r18_F04A_fastener_{i}" for i in range(1, 7))],
        "F03A": ["main_r18_F03A_ring", "main_r18_F03A_disc",
                 "main_r18_F03A_fastener_1", "main_r18_F03A_fastener_2"],
        "F04B": ["main_r18_F04B_cover", *(f"main_r18_F04B_fastener_{i}" for i in range(1, 5))],
        "F05": ["main_r18_F05_terminal_left", "main_r18_F05_center_strip",
                "main_r18_F05_terminal_right", "main_r18_F05_fastener_1",
                "main_r18_F05_fastener_2"],
        "F10": ["booster_r18_F10_cover", *(f"booster_r18_F10_fastener_{i}" for i in range(1, 4))],
        "F03B": ["booster_r18_F03B_keyed_cap"],
    })[variant]
    host_label = BOOSTER_HOST if variant == "booster_F10_F03B" else MAIN_HOST
    selected_features = feature_map[1:]
    missing = [label for label in [host_label, *selected_features] if label not in by_label]
    if missing:
        raise ValueError((variant, "full access model is missing selected crop leaves", missing))
    body = by_label[host_label]
    body_bounds = body.bounding_box()
    clip = bd.Box(bounds[1] - bounds[0], body_bounds.size.Y + 2.0,
                  body_bounds.size.Z + 2.0).translate(
                      ((bounds[0] + bounds[1]) / 2.0,
                       (body_bounds.min.Y + body_bounds.max.Y) / 2.0,
                       (body_bounds.min.Z + body_bounds.max.Z) / 2.0))
    cropped_body = body & clip
    if not cropped_body or not cropped_body.is_valid or len(cropped_body.solids()) != 1:
        raise ValueError((variant, "selected host crop is empty, invalid, or split"))
    cropped_body.label = f"{host_label}_r18_crop_{variant}"
    cropped_body.color = body.color
    crop_parts = [cropped_body, *(by_label[label] for label in selected_features)]
    for part in crop_parts[1:]:
        if part.bounding_box().min.X < bounds[0] - 0.05 or \
                part.bounding_box().max.X > bounds[1] + 0.05:
            raise ValueError((variant, part.label, "selected detail escapes its authorized axial crop"))
    crop = bd.Compound(children=crop_parts, label=f"Halberd_R18_Access_{variant}")
    selected_labels = [cropped_body.label, *selected_features]
    return crop, selected_labels, list(bounds)


def metadata_crop_labels(variant):
    body = BOOSTER_HOST if variant == "booster_F10_F03B" else MAIN_HOST
    crop_body = f"{body}_r18_crop_{variant}"
    data = {
        "F02": [crop_body, "main_r18_F02_cover",
                *(f"main_r18_F02_fastener_{i}" for i in range(1, 5))],
        "forward_F04A_F03A": [crop_body, "main_r18_F04A_cover",
                              *(f"main_r18_F04A_fastener_{i}" for i in range(1, 7)),
                              "main_r18_F03A_ring", "main_r18_F03A_disc",
                              "main_r18_F03A_fastener_1", "main_r18_F03A_fastener_2"],
        "F04B": [crop_body, "main_r18_F04B_cover",
                 *(f"main_r18_F04B_fastener_{i}" for i in range(1, 5))],
        "F05": [crop_body, "main_r18_F05_terminal_left", "main_r18_F05_center_strip",
                "main_r18_F05_terminal_right", "main_r18_F05_fastener_1",
                "main_r18_F05_fastener_2"],
        "booster_F10_F03B": [crop_body, "booster_r18_F10_cover",
                             *(f"booster_r18_F10_fastener_{i}" for i in range(1, 4)),
                             "booster_r18_F03B_keyed_cap"],
    }
    return data[variant]


def moved_booster_variant(full_shape, delta_x=-340.0):
    """Separate the booster in axial -X while preserving all full-build leaves."""
    moved = []
    for part in full_shape.children:
        label = part.label
        if label == BOOSTER_HOST or label.startswith("booster_"):
            copy = part.moved(bd.Location((delta_x, 0.0, 0.0)))
            copy.label = label
            copy.color = part.color
            moved.append(copy)
        else:
            moved.append(part)
    return bd.Compound(children=moved, label="Halberd_R18_Access_Separated_Booster_Minus_340X")
