"""Measured R18 F02 native shoulder feasibility; does not build other features."""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE_STEP = ROOT / "STEP" / "halberd_r18_f02_probe.step"
PROBE_SIDECAR = Path(str(PROBE_STEP) + ".json")
REPORT_PATH = ROOT / "reviews" / "halberd_r18_f02_probe_checks.json"
sys.path.insert(0, str(ROOT / "src"))

from cadgen import build123d as bd, read_scene
from cadgen.geometry import boundary_edges, self_intersections, topology_errors
from halberd_r18_access_shapes import (
    APPROVED_BASE_HASH,
    BASELINE_STEP,
    build_f02_native_preflight,
    load_manifest,
    load_saved_parts,
)


TOL = 0.05


def volume(shape):
    return shape.volume if shape else 0.0


def boxes_overlap(a, b):
    aa, bb = a.bounding_box(optimal=False), b.bounding_box(optimal=False)
    return not (aa.max.X < bb.min.X or bb.max.X < aa.min.X or
                aa.max.Y < bb.min.Y or bb.max.Y < aa.min.Y or
                aa.max.Z < bb.min.Z or bb.max.Z < aa.min.Z)


def common_face_area(a, b):
    areas = []
    for first in a.faces():
        for second in b.faces():
            if boxes_overlap(first, second):
                common = first & second
                if common and common.area > 0.001:
                    areas.append(common.area)
    return max(areas, default=0.0)


def assert_native_single(shape, label):
    solids = shape.solids()
    assert shape.is_valid, (label, "invalid")
    assert len(solids) == 1, (label, "expected one solid", len(solids))
    assert solids[0].volume > 0.0, (label, "non-positive volume")
    assert not topology_errors(shape), (label, "topology errors")
    assert all(not boundary_edges(shell) for shell in shape.shells()), (label, "open shell")
    assert not self_intersections(shape), (label, "self-intersection")


def _probe_crop(host):
    bounds = host.bounding_box()
    return bd.Box(190.0, bounds.size.Y + 2.0, bounds.size.Z + 2.0).translate(
        (900.0, (bounds.min.Y + bounds.max.Y) / 2.0,
         (bounds.min.Z + bounds.max.Z) / 2.0))


def _color_text(shape):
    color = shape.color
    return None if color is None else str(color)


def check_saved_probe(proto, source_parts, source_scene):
    assert PROBE_STEP.is_file(), ("missing saved F02 probe STEP", str(PROBE_STEP))
    assert PROBE_SIDECAR.is_file(), ("missing F02 probe material sidecar", str(PROBE_SIDECAR))
    saved_scene = read_scene(PROBE_STEP)
    saved_leaves = tuple(saved_scene.leaves())
    saved_parts = {leaf.label: saved_scene.resolve(leaf.ref).shape()
                   for leaf in saved_leaves}
    expected_labels = {
        "main_body_intake_r12_r18_access_cut",
        "r18_F02_cover",
        *(f"r18_F02_fastener_{index}" for index in range(1, 5)),
    }
    assert len(saved_leaves) == 6 and len(saved_parts) == 6, \
        ("saved F02 focus must contain exactly six unique parts", len(saved_leaves),
         len(saved_parts))
    assert set(saved_parts) == expected_labels, \
        ("saved F02 focus labels/source identity", sorted(saved_parts), sorted(expected_labels))

    expected_host = proto.host_after & _probe_crop(proto.host_before)
    expected_host.label = "main_body_intake_r12_r18_access_cut"
    expected_host.color = proto.host_after.color
    assert _color_text(source_parts["main_body_intake_r12"]) == \
           _color_text(proto.host_before), "F02 source host color changed before focus generation"
    expected = {expected_host.label: expected_host}
    expected.update((part.label, part) for part in proto.parts)
    saved_single = {}
    source_delta = {}
    saved_contacts = {}
    for label in sorted(expected_labels):
        actual, target = saved_parts[label], expected[label]
        assert_native_single(actual, f"saved {label}")
        added = volume(actual - target)
        missing = volume(target - actual)
        source_delta[label] = {"saved_extra_mm3": added, "source_missing_mm3": missing}
        assert added < TOL and missing < TOL, \
            (label, "saved geometry differs from baseline-derived F02 focus", added, missing)
        assert _color_text(actual) == _color_text(target), \
            (label, "native STEP color differs from source", _color_text(actual),
             _color_text(target))
        saved_single[label] = _color_text(actual)
        if label != expected_host.label:
            assert volume(actual & saved_parts[expected_host.label]) < TOL, \
                (label, "overlaps saved pocketed host")
            area = common_face_area(actual, saved_parts[expected_host.label])
            assert area > 0.001, (label, "saved part lacks common support face", area)
            assert actual.distance_to(saved_parts[expected_host.label]) < 1e-4, \
                (label, "saved part is not skin-supported")
            saved_contacts[label] = area

    saved_pair_overlaps = {}
    for first, second in combinations(saved_parts.values(), 2):
        overlap = volume(first & second)
        saved_pair_overlaps[f"{first.label}/{second.label}"] = overlap
        assert overlap < TOL, (first.label, second.label, "saved part overlap", overlap)

    saved_slot_fill = {}
    for head, slot in zip(proto.parts[1:], proto.slot_cutters):
        overlap = volume(saved_parts[head.label] & slot)
        saved_slot_fill[head.label] = overlap
        assert overlap < TOL, (head.label, "saved slot is filled", overlap)

    host_bounds = saved_parts[expected_host.label].bounding_box()
    assert abs(host_bounds.min.X - 805.0) < TOL and \
           abs(host_bounds.max.X - 995.0) < TOL, \
        ("saved F02 focus axial crop", host_bounds.min.X, host_bounds.max.X)

    sidecar = json.loads(PROBE_SIDECAR.read_text(encoding="utf-8"))
    appearance = sidecar.get("appearance", {})
    material_definitions = appearance.get("materials", {})
    material_assignments = appearance.get("assignments", {})
    assert {"detail_paint", "detail_metal"} <= set(material_definitions), \
        ("F02 material sidecar lost the approved original definitions",
         sorted(material_definitions))
    assert set(material_assignments.values()) >= {"detail_paint", "detail_metal"}, \
        ("F02 material sidecar is missing cover/fastener assignments",
         material_assignments)

    return {
        "status": "passed",
        "saved_step": str(PROBE_STEP),
        "saved_document_hash": saved_scene.document_hash,
        "source_document_hash": source_scene.document_hash,
        "saved_part_count": len(saved_parts),
        "saved_part_labels": sorted(saved_parts),
        "axial_crop_mm": [host_bounds.min.X, host_bounds.max.X],
        "saved_geometry_source_delta_mm3": source_delta,
        "saved_support_common_face_area_mm2": saved_contacts,
        "saved_part_pair_overlaps_mm3": saved_pair_overlaps,
        "saved_head_slot_overlap_mm3": saved_slot_fill,
        "saved_native_colors": saved_single,
        "sidecar_material_names": sorted(material_definitions),
        "sidecar_assignments": material_assignments,
    }


def run():
    manifest = load_manifest()
    scene, parts = load_saved_parts()
    assert scene.document_hash == APPROVED_BASE_HASH, \
        ("saved layout base hash mismatch", scene.document_hash)
    assert len(parts) == 28, ("saved layout base count", len(parts))
    host = parts["main_body_intake_r12"]
    proto = build_f02_native_preflight(host, manifest)

    assert_native_single(proto.host_after, "F02 changed main host")
    assert_native_single(proto.pocket_cutter, "F02 local pocket cutter")
    assert len(proto.parts) == 5
    for part in proto.parts:
        assert_native_single(part, part.label)
        assert volume(part - host) < TOL, (part.label, "outside original host envelope")
        assert volume(part & proto.host_after) < TOL, (part.label, "overlaps pocketed host")
        assert part.distance_to(proto.host_after) < 1e-4, (part.label, "no skin support")
        assert common_face_area(part, proto.host_after) > 0.001, \
            (part.label, "missing common support face")
    for first, second in combinations(proto.parts, 2):
        assert volume(first & second) < TOL, \
            (first.label, second.label, "detail/detail overlap")

    cutters = proto.pocket_cutter
    for seat in proto.seat_cutters:
        assert volume(host & seat) > 0.0, (seat.label, "does not cut actual skin")
        cutters = cutters + seat
    removed = host - proto.host_after
    expected_removed = host & cutters
    assert volume(removed - expected_removed) < TOL
    assert volume(expected_removed - removed) < TOL
    assert volume(proto.host_after - host) < TOL, "host gained material"
    assert volume(removed) > 0.0

    slot_fill = {}
    for head, slot in zip(proto.parts[1:], proto.slot_cutters):
        slot_fill[head.label] = volume(head & slot)
        assert slot_fill[head.label] < TOL, (head.label, "slot is filled")
    sites = proto.parameters["screw_sites"]
    assert len(sites) == 4
    assert max(site["projection_error_mm"] for site in sites) < 0.35
    assert all(sum(value * value for value in site["outward_normal"]) > 0.999
               for site in sites)
    assert all(site["outward_normal"][2] >= 0.25 for site in sites)
    assert min(site["remaining_wall_after_seat_mm"] for site in sites) > 0.25
    skin_samples = proto.parameters["skin_samples"]
    assert len(skin_samples) == 9
    radii = [row["radius_mm"] for row in skin_samples]
    assert max(radii) - min(radii) > 0.01, "F02 sample did not reach a curved shoulder"
    assert min(row["backed_wall_mm"] for row in skin_samples) > 0.8
    assert max(row["projection_error_mm"] for row in skin_samples) < 0.35
    assert all(row["outward_normal"][2] >= 0.25 for row in skin_samples)

    removed_bounds = removed.bounding_box()
    local_outline = proto.parameters["outline_local_mm"]
    feature_x = proto.parameters["center_x_mm"]
    x_limits = [feature_x + min(point[0] for point in local_outline),
                feature_x + max(point[0] for point in local_outline)]
    tangent_limits = [min(point[1] for point in local_outline),
                      max(point[1] for point in local_outline)]
    assert removed_bounds.min.X >= x_limits[0] - TOL and \
           removed_bounds.max.X <= x_limits[1] + TOL
    assert removed_bounds.min.Y >= tangent_limits[0] - TOL and \
           removed_bounds.max.Y <= tangent_limits[1] + TOL

    report = {
        "status": "F02_NATIVE_PREFLIGHT_PASS",
        "saved_base_hash": scene.document_hash,
        "base_leaf_count": len(parts),
        "host": proto.host_label,
        "native_surface": {
            "clock_degrees": proto.parameters["clock_degrees"],
            "center_skin_radius_mm": proto.parameters["skin_center_radius_mm"],
            "sampled_skin_radius_range_mm": [min(radii), max(radii)],
            "sampled_skin_points": skin_samples,
            "minimum_available_backing_mm": min(
                row["backed_wall_mm"] for row in skin_samples),
            "maximum_native_projection_error_mm": max(
                row["projection_error_mm"] for row in skin_samples),
        },
        "feature": {
            "outline_vertex_count": len(proto.parameters["outline_local_mm"]),
            "pocket_depth_mm": proto.parameters["pocket_depth_mm"],
            "cover_setback_mm": proto.parameters["cover_setback_mm"],
            "perimeter_gap_mm": proto.parameters["perimeter_gap_mm"],
            "pocket_volume_mm3": proto.parameters["pocket_volume_mm3"],
            "pocket_bounds_mm": proto.parameters["pocket_bounds_mm"],
            "screw_support": sites,
            "part_labels": [part.label for part in proto.parts],
            "part_support_common_face_area_mm2": {
                part.label: common_face_area(part, proto.host_after)
                for part in proto.parts
            },
            "host_removed_volume_mm3": volume(removed),
            "localized_host_cut_bounds_mm": [removed_bounds.min.X,
                                               removed_bounds.min.Y,
                                               removed_bounds.min.Z,
                                               removed_bounds.max.X,
                                               removed_bounds.max.Y,
                                               removed_bounds.max.Z],
        },
        "checks": {
            "valid_closed_positive_single_native_solids": 7,
            "host_envelope_additions_mm3": volume(proto.host_after - host),
            "cover/head_outside_original_host_mm3": {
                part.label: volume(part - host) for part in proto.parts
            },
            "cover/head_overlap_with_pocketed_host_mm3": {
                part.label: volume(part & proto.host_after) for part in proto.parts
            },
            "feature_part_pair_overlaps_mm3": {
                f"{first.label}/{second.label}": volume(first & second)
                for first, second in combinations(proto.parts, 2)
            },
            "head_slot_overlap_mm3": slot_fill,
        },
        "saved_probe_artifact": "not present yet",
    }
    if PROBE_STEP.is_file():
        report["saved_probe_artifact"] = check_saved_probe(proto, parts, scene)
        report["status"] = "F02_SAVED_PROBE_PASS"
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"PASS: {report['status']}; report={REPORT_PATH}")


if __name__ == "__main__":
    run()
