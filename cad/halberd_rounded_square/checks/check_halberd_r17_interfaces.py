"""R17 local interface feasibility and saved-artifact verification."""
from __future__ import annotations

import json
import math
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cadgen import build123d as bd, read_scene
from cadgen.geometry import boundary_edges, self_intersections, topology_errors
from halberd_r17_interface_shapes import (
    FASTENER_HEAD_TOP_RADIUS,
    FASTENER_SEAT_DEPTH,
    FASTENER_TOP_RECESS,
    FIN_INSET_DEPTH,
    REVIEW_FIXTURE_TRANSLATIONS,
    build_review_artifact,
    build_r17_prototypes,
    load_r16_parts,
)


ARTIFACTS = {
    "main_fin": "halberd_r17_interfaces_main_fin",
    "booster_fin": "halberd_r17_interfaces_booster_fin",
    "nozzles": "halberd_r17_interfaces_nozzles",
}
REPORT_PATH = ROOT / "reviews" / "halberd_r17_interface_checks.json"
VOLUME_TOLERANCE = 0.01
IDENTITY_TOLERANCE = 0.05


def volume(shape):
    return shape.volume if shape else 0.0


def identical(actual, expected, tolerance=IDENTITY_TOLERANCE):
    assert volume(actual - expected) < tolerance, "unexpected/missing comparison geometry"
    assert volume(expected - actual) < tolerance, "comparison is missing expected geometry"


def boxes_overlap(a, b):
    aa, bb = a.bounding_box(optimal=False), b.bounding_box(optimal=False)
    return not (aa.max.X < bb.min.X or bb.max.X < aa.min.X or
                aa.max.Y < bb.min.Y or bb.max.Y < aa.min.Y or
                aa.max.Z < bb.min.Z or bb.max.Z < aa.min.Z)


def bbox_gap_lower_bound(a, b):
    aa, bb = a.bounding_box(optimal=False), b.bounding_box(optimal=False)
    gaps = (
        max(0.0, aa.min.X - bb.max.X, bb.min.X - aa.max.X),
        max(0.0, aa.min.Y - bb.max.Y, bb.min.Y - aa.max.Y),
        max(0.0, aa.min.Z - bb.max.Z, bb.min.Z - aa.max.Z),
    )
    return math.sqrt(sum(gap * gap for gap in gaps))


def common_face_areas(a, b):
    areas = []
    for face_a in a.faces():
        for face_b in b.faces():
            if not boxes_overlap(face_a, face_b):
                continue
            common = face_a & face_b
            if common and common.area > 0.001:
                areas.append(common.area)
    return areas


def available_wall(host, point, outward, max_depth=12.0):
    point = bd.Vector(point)
    outward = bd.Vector(outward).normalized()
    inside = lambda depth: host.is_inside(point - outward * depth)
    if not inside(0.01):
        raise AssertionError(("surface point is not backed by its host", tuple(point)))
    lo = 0.01
    hi = lo
    step = 0.05
    while hi < max_depth and inside(hi):
        lo = hi
        hi = min(max_depth, hi + step)
    if inside(hi):
        raise AssertionError(("support thickness exceeds probe bound", tuple(point), max_depth))
    for _ in range(32):
        mid = (lo + hi) / 2.0
        if inside(mid):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def radial_boundary(host, x, clock_degrees, inner_radius, max_radius):
    angle = math.radians(clock_degrees)
    inside = lambda radius: host.is_inside((x, radius * math.sin(angle),
                                            radius * math.cos(angle)))
    if not inside(inner_radius):
        raise AssertionError(("lip support probe did not enter host", x, clock_degrees,
                              inner_radius))
    lo = inner_radius
    hi = lo
    while hi < max_radius and inside(hi):
        lo = hi
        hi = min(max_radius, hi + 0.5)
    if inside(hi):
        raise AssertionError(("no radial exit found", x, clock_degrees, max_radius))
    for _ in range(36):
        mid = (lo + hi) / 2.0
        if inside(mid):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def local_cut_facts(proto):
    old = proto.host_before
    new = proto.host_after
    assert old.is_valid and len(old.solids()) == 1
    assert new.is_valid and len(new.solids()) == 1
    assert volume(new - old) < VOLUME_TOLERANCE, (proto.key, "host gained volume")
    cutter_union = proto.cutters[0]
    for cutter in proto.cutters[1:]:
        cutter_union = cutter_union + cutter
    assert volume(old & proto.cutters[0]) > 0.0, (proto.key, "primary pocket misses host")
    for seat in proto.seat_cutters:
        assert volume(old & seat) > 0.0, (proto.key, seat.label, "seat misses host")
    removed = old - new
    expected_removed = old & cutter_union
    identical(removed, expected_removed)
    assert volume(removed) > 0.0, (proto.key, "cutters did not remove host material")
    assert len(proto.parts) == (5 if "fin" in proto.key else 9), proto.key
    for part in proto.parts:
        assert part.is_valid and len(part.solids()) == 1 and part.solids()[0].volume > 0
        assert volume(part - old) < VOLUME_TOLERANCE, (proto.key, part.label, "outside old envelope")
        assert volume(part & new) < VOLUME_TOLERANCE, (proto.key, part.label, "overlaps cut host")
        assert new.distance_to(part) < 1e-4, (proto.key, part.label, "no support contact")
        assert max(common_face_areas(part, new), default=0.0) > 0.001, \
            (proto.key, part.label, "missing common support face")
    for first, second in combinations(proto.parts, 2):
        assert volume(first & second) < VOLUME_TOLERANCE, \
            (proto.key, first.label, second.label, "detail/detail overlap")
    head_parts = proto.parts[1:] if "fin" in proto.key else proto.parts[1:]
    assert len(head_parts) == len(proto.slot_cutters) == (4 if "fin" in proto.key else 8)
    for head, slot, site in zip(head_parts, proto.slot_cutters,
                                proto.parameters["screw_sites"]):
        point = bd.Vector(site.get("point_mm", site.get("center_mm")))
        normal = bd.Vector(site.get("outward_normal", (-1, 0, 0))).normalized()
        assert volume(head & slot) < VOLUME_TOLERANCE, (proto.key, head.label, "slot is filled")
        slot_probe = point - normal * (FASTENER_TOP_RECESS + 0.10)
        head_material_probe = point - normal * 0.72
        assert not head.is_inside(slot_probe), (proto.key, head.label, "slot is not open")
        assert head.is_inside(head_material_probe), (proto.key, head.label, "head material missing")
    return {
        "host_label": proto.host_label,
        "cutter_count": len(proto.cutters),
        "detail_count": len(proto.parts),
        "removed_volume_mm3": volume(removed),
        "host_before_mm3": volume(old),
        "host_after_mm3": volume(new),
        "detail_parts": [part.label for part in proto.parts],
    }


def fin_feasibility(proto):
    face = proto.host_before.faces()[proto.parameters["face_index"]]
    v = proto.parameters["center_uv"][1]
    wall_rows = []
    for site in proto.parameters["screw_sites"]:
        u = site["u"]
        point = face.position_at(u, v)
        normal = face.normal_at(u, v).normalized()
        wall = available_wall(proto.host_before, point, normal)
        remaining = wall - FASTENER_SEAT_DEPTH
        assert remaining > 0.25, (proto.key, u, wall, remaining, "back wall too thin")
        wall_rows.append({"u": u, "available_host_thickness_mm": wall,
                          "remaining_wall_after_seat_mm": remaining})
    assert len(wall_rows) == 4
    assert proto.parameters["patch_area_mm2"] > 0.0
    return {
        "patch_area_mm2": proto.parameters["patch_area_mm2"],
        "patch_bounds_mm": proto.parameters["patch_bounds_mm"],
        "strip_dimensions_mm": [proto.parameters["strip_length_mm"],
                                 proto.parameters["strip_width_mm"]],
        "strip_recess_mm": FIN_INSET_DEPTH,
        "four_site_thickness": wall_rows,
    }


def nozzle_feasibility(proto):
    p = proto.parameters
    x = p["mouth_x_mm"] + 0.1
    outer_samples = []
    bore_samples = []
    for site in p["screw_sites"]:
        clock = site["clock_degrees"]
        boundary = radial_boundary(proto.host_before, x, clock,
                                   p["cavity_radius_mm"] + 1.0, 200.0)
        outer_samples.append({"clock_degrees": clock,
                              "measured_outer_support_radius_mm": boundary})
        angle = math.radians(clock)
        bore_point = (x, (p["cavity_radius_mm"] - 1.0) * math.sin(angle),
                      (p["cavity_radius_mm"] - 1.0) * math.cos(angle))
        assert not proto.host_before.is_inside(bore_point), \
            (proto.key, clock, "mouth bore baseline is already occluded")
        assert not proto.host_after.is_inside(bore_point), \
            (proto.key, clock, "pilot cut occluded the open bore")
        bore_samples.append(clock)
    min_support = min(row["measured_outer_support_radius_mm"] for row in outer_samples)
    head_outer = p["screw_radius_mm"] + FASTENER_HEAD_TOP_RADIUS
    outer_margin = min_support - head_outer
    ring_clearance = p["ring_cut_radii_mm"][0] - p["cavity_radius_mm"]
    ring_to_heads = (p["screw_radius_mm"] - FASTENER_HEAD_TOP_RADIUS
                     - p["ring_cut_radii_mm"][1])
    assert ring_clearance >= 1.0, (proto.key, ring_clearance, "ring too close to open bore")
    assert outer_margin > 0.5, (proto.key, outer_margin, "head too close to lip boundary")
    assert ring_to_heads > 0.5, (proto.key, ring_to_heads, "ring/head radial clearance")
    assert len(outer_samples) == len(bore_samples) == 8
    return {
        "measured_min_outer_support_radius_mm": min_support,
        "head_outer_radius_mm": head_outer,
        "minimum_head_to_boundary_mm": outer_margin,
        "ring_to_open_bore_mm": ring_clearance,
        "ring_to_head_radial_gap_mm": ring_to_heads,
        "eight_clocked_support_radii": outer_samples,
        "bore_open_samples_degrees": bore_samples,
    }


def run_preflight():
    baseline_scene, baseline = load_r16_parts()
    prototypes = build_r17_prototypes(baseline)
    rows = {}
    for key, proto in prototypes.items():
        row = local_cut_facts(proto)
        row["feasibility"] = fin_feasibility(proto) if "fin" in key else nozzle_feasibility(proto)
        rows[key] = row
    report = {
        "status": "PREFLIGHT_PASS",
        "baseline_document_hash": baseline_scene.document_hash,
        "units": "mm and mm^3",
        "prototypes": rows,
    }
    print(json.dumps(report, indent=2))


def validate_saved_artifact(name, expected):
    scene = read_scene(ROOT / "STEP" / f"{name}.step")
    leaves = tuple(scene.leaves())
    saved = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in leaves}
    assert len(saved) == len(leaves), f"{name}: duplicate leaf labels"
    assert set(saved) == set(expected), (name, "saved/expected labels differ",
                                         sorted(set(saved) ^ set(expected)))
    sidecar_path = ROOT / "STEP" / f"{name}.step.json"
    sidecar = None
    if sidecar_path.exists():
        sidecar = json.loads(sidecar_path.read_text())
        assert sidecar["documentHash"] == scene.document_hash, f"{name}: stale STEP sidecar"
    for index, leaf in enumerate(leaves, 1):
        shape = saved[leaf.label]
        assert len(shape.solids()) == 1, (name, leaf.label, "expected one solid")
        solid = shape.solids()[0]
        assert solid.volume > 0.0, (name, leaf.label, "nonpositive solid")
        assert not topology_errors(shape), (name, leaf.label, "topology errors")
        assert all(not boundary_edges(shell) for shell in shape.shells()), \
            (name, leaf.label, "open shell")
        assert not self_intersections(shape), (name, leaf.label, "self-intersection")
        identical(shape, expected[leaf.label])
        actual_color, expected_color = tuple(shape.color), tuple(expected[leaf.label].color)
        assert len(actual_color) == len(expected_color) and all(
            abs(a - b) < 1e-6 for a, b in zip(actual_color, expected_color)), \
            (name, leaf.label, "saved color changed", actual_color, expected_color)
        print(f"  {name}: {index}/{len(leaves)} {leaf.label}", flush=True)
    return scene, saved, sidecar


def run_full():
    REPORT_PATH.write_text(json.dumps({"status": "CHECKS_INCOMPLETE"}, indent=2) + "\n")
    baseline_scene, baseline = load_r16_parts()
    prototypes = build_r17_prototypes(baseline)
    cut_reports = {key: local_cut_facts(proto) for key, proto in prototypes.items()}
    feasibility = {
        key: fin_feasibility(proto) if "fin" in key else nozzle_feasibility(proto)
        for key, proto in prototypes.items()
    }

    expected_count = {"main_fin": 7, "booster_fin": 7, "nozzles": 24}
    saved_reports = {}
    saved_shapes = {}
    saved_sidecars = {}
    for kind, name in ARTIFACTS.items():
        model, expected, rebuilt, _ = build_review_artifact(kind)
        assert model.is_valid
        scene, saved, sidecar = validate_saved_artifact(name, expected)
        assert len(saved) == expected_count[kind], (name, len(saved), expected_count[kind])
        saved_reports[name] = {"document_hash": scene.document_hash,
                               "leaf_count": len(saved),
                               "material_sidecar_present": sidecar is not None,
                               "labels": sorted(saved)}
        saved_shapes[name] = saved
        saved_sidecars[name] = sidecar

    # No new local detail may interfere with any non-target baseline component.
    clearance_pairs = 0
    clearance_candidates = 0
    nearby_pairs = 0
    min_clearance = {}
    proximity_window_mm = 100.0
    for proto in prototypes.values():
        for detail in proto.parts:
            for other_label, other in baseline.items():
                if other_label == proto.host_label or not boxes_overlap(detail, other):
                    if (other_label == proto.host_label or
                            bbox_gap_lower_bound(detail, other) > proximity_window_mm):
                        continue
                else:
                    clearance_candidates += 1
                    overlap = volume(detail & other)
                    assert overlap < VOLUME_TOLERANCE, \
                        (proto.key, detail.label, other_label, overlap,
                         "other original part overlap")
                nearby_pairs += 1
                gap = detail.distance_to(other)
                key = f"{proto.key}/{detail.label}/{other_label}"
                min_clearance[key] = gap
                assert gap > 0.0, (proto.key, detail.label, other_label, "zero clearance")
            clearance_pairs += len(baseline) - 1

    # The saved display crops preserve each exact changed host and detail placement.
    for kind, proto_key in (("main_fin", "main_fin"),
                            ("booster_fin", "booster_fin")):
        proto = prototypes[proto_key]
        host_label = "r17_main_fin_host_cut" if kind == "main_fin" \
            else "r17_booster_fin_host_cut"
        crop_host = saved_shapes[ARTIFACTS[kind]][host_label]
        assert crop_host.volume > 0.0
    for label in ("r17_main_nozzle_host_cut", "r17_booster_nozzle_host_cut"):
        assert any(label in report["labels"] for report in saved_reports.values()), label

    report = {
        "status": "PASS",
        "baseline_document_hash": baseline_scene.document_hash,
        "saved_artifacts": saved_reports,
        "native_host_cut_results": cut_reports,
        "measured_feasibility": feasibility,
        "other_original_part_clearances": {
            "bbox_candidate_pairs_tested_exactly": clearance_candidates,
            "nearby_pairs_within_100mm_tested_exactly": nearby_pairs,
            "baseline_label_pair_budget": clearance_pairs,
            "minimum_clearance_mm": min_clearance,
        },
        "saved_geometry_placements_checked": sum(row["leaf_count"]
                                                  for row in saved_reports.values()),
        "review_fixture_translations_mm": REVIEW_FIXTURE_TRANSLATIONS,
        "unchanged_r16_sources_or_artifacts_modified": False,
        "propagation_performed": False,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("PASS: exact localized host cuts, support contacts, wall thickness,"
          " envelope/bore preservation, clearances, and saved STEP topology.")


if __name__ == "__main__":
    if "--preflight" in sys.argv:
        run_preflight()
    else:
        run_full()
