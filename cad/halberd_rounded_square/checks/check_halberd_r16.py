"""R16 preflight and saved-artifact checks for the nose/body joint prototype."""
from __future__ import annotations

import json
import math
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cadgen import build123d as bd, read_scene, srgb
from cadgen.geometry import boundary_edges, self_intersections, topology_errors
from halberd_r16_shapes import fastener_seat, joint_pocket, liner_shape

MAIN = "main_body_intake_r12"
OGIVE = "main_ogive"
JOINT_PARTS = ("main_joint_liner_1", *(f"main_joint_fastener_{i}" for i in range(1, 5)))
FASTENERS = JOINT_PARTS[1:]
FOCUS_LABELS = (MAIN, OGIVE, *JOINT_PARTS)
CLOCKS = (0., 90., 180., 270.)
REFERENCE_PARTS = (
    "body_section_5", "near_side_panel_border", "near_side_dark_panel",
    "front_section_seam_1", "front_section_seam_2",
    *(f"front_joint_fastener_{face}_{row}"
      for face in range(1, 5) for row in (1, 2)),
)
REPORT_PATH = ROOT / "reviews" / "halberd_r16_checks.json"


def load(name):
    scene = read_scene(ROOT / "STEP" / f"{name}.step")
    leaves = tuple(scene.leaves())
    parts = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in leaves}
    assert len(parts) == len(leaves), f"duplicate labels in {name}"
    return scene, parts


def volume(shape):
    return shape.volume if shape else 0.


def close(actual, expected, tolerance=.002):
    assert abs(actual - expected) < tolerance, (actual, expected, tolerance)


def color_close(actual, expected, tolerance=1e-6):
    assert len(actual) == len(expected) and all(abs(a - b) < tolerance
                                                 for a, b in zip(actual, expected)), \
        (actual, expected, tolerance)


def identical(a, b, tolerance=.05):
    assert volume(a - b) < tolerance, "geometry missing from comparison"
    assert volume(b - a) < tolerance, "unexpected extra geometry"


def radial_point(x, radius, clock):
    angle = math.radians(clock)
    return (x, radius * math.sin(angle), radius * math.cos(angle))


def skin_radius(solid, x, clock):
    lo, hi = 90., 100.
    assert solid.is_inside(radial_point(x, lo, clock))
    assert not solid.is_inside(radial_point(x, hi, clock))
    for _ in range(50):
        mid = (lo + hi) / 2
        if solid.is_inside(radial_point(x, mid, clock)):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def preflight():
    _, baseline = load("halberd_r15")
    body = baseline[MAIN]
    solid = body.solids()[0]
    pocket = joint_pocket()
    annular = body - pocket
    hole_tools = [fastener_seat(clock) for clock in CLOCKS]
    cut_body = annular
    for tool in hole_tools:
        cut_body = cut_body - tool
    radii = {str(int(clock)): {
        str(x): skin_radius(solid, x, clock)
        for x in (1075., 1078., 1081., 1083.7, 1084., 1084.9)
    } for clock in CLOCKS}
    hole_cuts = [volume(body & tool) for tool in hole_tools]
    result = {
        "baseline_document_hash": read_scene(ROOT / "STEP" / "halberd_r15.step").document_hash,
        "original_main_solids": len(body.solids()),
        "main_after_ring_and_four_seats_solids": len(cut_body.solids()),
        "main_after_ring_and_four_seats_valid": cut_body.is_valid,
        "main_volume_removed_mm3": volume(body) - volume(cut_body),
        "ring_intersection_mm3": volume(body & pocket),
        "ring_bounds_mm": {
            "x": [pocket.bounding_box().min.X, pocket.bounding_box().max.X],
            "inner_radius_mm": 94.4,
            "outer_cutter_radius_mm": 120.,
        },
        "actual_saved_skin_radius_at_x1078_mm": radii,
        "blind_seat_intersections_mm3": hole_cuts,
        "blind_seat_count": len(hole_tools),
    }
    assert len(body.solids()) == 1 and body.is_valid
    assert len(cut_body.solids()) == 1 and cut_body.is_valid
    assert result["main_volume_removed_mm3"] > 0.
    assert result["ring_intersection_mm3"] > 0.
    assert all(v > 0. for v in hole_cuts)
    for clock, samples in radii.items():
        for x, radius in samples.items():
            assert 94.65 < radius < 95.1, (clock, x, radius, "unexpected local skin extent")
    print(json.dumps(result, indent=2))


def boxes_overlap(a, b):
    aa, bb = a.bounding_box(), b.bounding_box()
    return not (aa.max.X < bb.min.X or bb.max.X < aa.min.X or
                aa.max.Y < bb.min.Y or bb.max.Y < aa.min.Y or
                aa.max.Z < bb.min.Z or bb.max.Z < aa.min.Z)


def common_face_areas(a, b):
    areas = []
    for face_a in a.faces():
        for face_b in b.faces():
            if not boxes_overlap(face_a, face_b):
                continue
            common = face_a & face_b
            if common and common.area > .001:
                areas.append(common.area)
    return areas


def validate_native(name, expected_count, require_materials=True):
    scene, parts = load(name)
    sidecar = None
    if require_materials:
        sidecar = json.loads((ROOT / "STEP" / f"{name}.step.json").read_text())
        assert sidecar["documentHash"] == scene.document_hash, f"{name}: stale material sidecar"
    rows = []
    leaves = tuple(scene.leaves())
    print(f"Checking {name}: {len(leaves)} saved placements", flush=True)
    for index, leaf in enumerate(leaves, 1):
        shape = parts[leaf.label]
        solids = shape.solids()
        assert len(solids) == 1, (name, leaf.label, "expected one solid")
        assert solids[0].volume > 0., (name, leaf.label, "non-positive solid")
        assert not topology_errors(shape), (name, leaf.label, "topology errors")
        assert all(not boundary_edges(shell) for shell in shape.shells()), \
            (name, leaf.label, "open shell")
        assert not self_intersections(shape), (name, leaf.label, "self-intersection")
        rows.append({"label": leaf.label, "ref": leaf.ref, "volume_mm3": solids[0].volume})
        if index % 10 == 0 or index == len(leaves):
            print(f"  {name}: {index}/{len(leaves)} ({leaf.label})", flush=True)
    assert len(rows) == expected_count, (name, len(rows), expected_count)
    return scene, parts, sidecar, rows


def appearance_by_label(scene, sidecar):
    refs = sidecar["appearance"]["assignments"]
    result = {}
    for leaf in scene.leaves():
        ref = leaf.ref.lstrip("#")
        if ref in refs:
            result[leaf.label] = refs[ref]
    return result


def resolved_material(sidecar, material_id):
    return sidecar["appearance"]["materials"][material_id]


def assert_detail_metal(sidecar, material_id, label):
    material = resolved_material(sidecar, material_id)
    assert material["name"] == "Small metallic hardware", (label, material)
    assert material["roughness"] == .38, (label, material)
    assert material["metalness"] == .65, (label, material)


def check_materials(full_scene, full_sidecar, baseline_scene, baseline_sidecar,
                    focus_sidecar, focus_scene):
    baseline_assignments = appearance_by_label(baseline_scene, baseline_sidecar)
    full_assignments = appearance_by_label(full_scene, full_sidecar)
    assert set(full_assignments) == set(baseline_assignments) | set(JOINT_PARTS)
    for label, old_id in baseline_assignments.items():
        new_id = full_assignments[label]
        old = resolved_material(baseline_sidecar, old_id)
        new = resolved_material(full_sidecar, new_id)
        assert old == new, (label, old, new)
    for label in JOINT_PARTS:
        assert_detail_metal(full_sidecar, full_assignments[label], label)

    focus_assignments = appearance_by_label(focus_scene, focus_sidecar)
    assert set(focus_assignments) == set(JOINT_PARTS)
    assert set(focus_sidecar["appearance"]["materials"]) == {"detail_metal"}, \
        "focus should contain only the joint's resolved material definition"
    for label in JOINT_PARTS:
        assert_detail_metal(focus_sidecar, focus_assignments[label], label)
    assert full_sidecar["documentHash"] == full_scene.document_hash
    assert focus_sidecar["documentHash"] == focus_scene.document_hash


def preflight_facts(body):
    solid = body.solids()[0]
    radii = {
        str(int(clock)): {
            str(x): skin_radius(solid, x, clock)
            for x in (1075., 1078., 1081., 1083.7, 1084., 1084.9)
        }
        for clock in CLOCKS
    }
    return radii


def check_reference_crop():
    print("Checking actual Kris source crop and saved crop validity", flush=True)
    source_path = ROOT.parent / "IRM-S4_Kris_PL10_Hybrid.step"
    source_scene = read_scene(source_path)
    crop_scene, crop_parts, _, crop_rows = validate_native(
        "kris_joint_reference", len(REFERENCE_PARTS), require_materials=False)
    assert set(crop_parts) == set(REFERENCE_PARTS)
    source_parts = {leaf.label: source_scene.resolve(leaf.ref).shape()
                    for leaf in source_scene.leaves() if leaf.label in REFERENCE_PARTS}
    assert set(source_parts) == set(REFERENCE_PARTS)
    clip = bd.Box(180., 180., 70.).translate((0., 0., 2411.))
    for label in REFERENCE_PARTS:
        expected = (source_parts[label] & clip).rotate(bd.Axis.Y, -90.).translate((2411., 0., 0.))
        identical(crop_parts[label], expected)
        assert tuple(crop_parts[label].color) == tuple(source_parts[label].color), label
    return {
        "source_hash": source_scene.document_hash,
        "crop_hash": crop_scene.document_hash,
        "labels": list(REFERENCE_PARTS),
        "valid_placements": len(crop_rows),
    }


def run_full():
    REPORT_PATH.write_text(json.dumps({"ok": False, "status": "Checks incomplete"}) + "\n")
    baseline_scene, baseline = load("halberd_r15")
    baseline_sidecar = json.loads((ROOT / "STEP" / "halberd_r15.step.json").read_text())
    assert baseline_sidecar["documentHash"] == baseline_scene.document_hash
    full_scene, full, full_sidecar, full_rows = validate_native("halberd_r16", 44)
    separated_scene, separated, separated_sidecar, separated_rows = validate_native(
        "halberd_r16_separated", 44)
    focus_scene, focused, focus_sidecar, focus_rows = validate_native(
        "halberd_r16_focus", 7)
    _, baseline_separated = load("halberd_r15_separated")

    assert set(full) == set(separated) == set(baseline) | set(JOINT_PARTS)
    assert set(focused) == set(FOCUS_LABELS)
    assert len(full) == len(separated) == 44 and len(focused) == 7

    old_main = baseline[MAIN]
    main = full[MAIN]
    assert tuple(main.color) == tuple(old_main.color), "main body finish changed"
    for label in (MAIN, *JOINT_PARTS):
        identical(full[label], separated[label])
        assert tuple(full[label].color) == tuple(separated[label].color), label
    for label, shape in baseline.items():
        if label == MAIN:
            continue
        identical(full[label], shape)
        assert tuple(full[label].color) == tuple(shape.color), label
        restored = separated[label].moved(bd.Location((340., 0., 0.))) \
            if label.startswith("booster") else separated[label]
        identical(full[label], restored)
        assert tuple(separated[label].color) == tuple(shape.color), label
        old_stage = baseline_separated[label].moved(bd.Location((340., 0., 0.))) \
            if label.startswith("booster") else baseline_separated[label]
        identical(full[label], old_stage)

    # The full-model body difference must be exactly the five authored cutters.
    removed = old_main - main
    tools = joint_pocket()
    seat_tools = [fastener_seat(clock) for clock in CLOCKS]
    for tool in seat_tools:
        tools = tools + tool
    expected_removed = old_main & tools
    identical(removed, expected_removed)
    assert volume(main - old_main) < .01, "main body gained volume"
    assert len(removed.solids()) == 5, "expected one ring cut and four disconnected blind seats"
    ring_tool = joint_pocket()
    ring_removed = old_main & ring_tool
    close(ring_tool.bounding_box().min.X, 1083.7)
    close(ring_tool.bounding_box().max.X, 1085.)
    seat_bounds = []
    for clock, tool in zip(CLOCKS, seat_tools):
        cut = old_main & tool
        assert volume(cut) > 0., (clock, "seat does not cut the actual saved skin")
        bb = tool.bounding_box()
        original_solid = old_main.solids()[0]
        modified_solid = main.solids()[0]
        assert original_solid.is_inside(radial_point(1078., 93.4, clock)), (clock, "missing body under blind floor")
        assert modified_solid.is_inside(radial_point(1078., 93.4, clock)), (clock, "blind floor was cut through")
        assert not modified_solid.is_inside(radial_point(1078., 93.6, clock)), (clock, "seat bore is missing")
        seat_bounds.append({"clock_degrees": clock, "volume_mm3": volume(cut),
                            "tool_bounds_mm": [bb.min.X, bb.min.Y, bb.min.Z,
                                               bb.max.X, bb.max.Y, bb.max.Z],
                            "blind_floor_radius_mm": 93.5,
                            "body_at_floor_interior_mm": 93.4})

    skin_radii = preflight_facts(old_main)
    skin_at_center = [skin_radii[str(int(clock))]["1078.0"] for clock in CLOCKS]
    skin_max = max(skin_at_center)
    countersink_outer_radius = 94.1 + 1.2
    assert countersink_outer_radius > skin_max, (countersink_outer_radius, skin_max)
    main_bounds = main.bounding_box()
    close(main_bounds.max.X, 1085.)
    liner = full["main_joint_liner_1"]
    liner_bounds = liner.bounding_box()
    close(liner_bounds.min.X, 1083.8)
    close(liner_bounds.max.X, 1084.9)
    close(liner_bounds.max.Y, 94.8)
    close(liner_bounds.max.Z, 94.8)
    identical(liner, liner_shape())
    liner_axial_gaps = [liner_bounds.min.X - 1083.7, 1085. - liner_bounds.max.X]
    assert all(abs(gap - .1) < .002 for gap in liner_axial_gaps)

    # New objects remain within the saved original skin, seat the body without
    # volume interference, and clear every legacy non-main component.
    contacts = {}
    baseline_pair_count = 0
    legacy_overlap_candidates = 0
    color_close(tuple(full[JOINT_PARTS[0]].color), tuple(srgb("#87939B")))
    for label in JOINT_PARTS:
        part = full[label]
        color_close(tuple(part.color), tuple(srgb("#87939B")))
        assert volume(part - old_main) < .01, (label, "outside original body skin")
        contact_volume = volume(part & main)
        assert contact_volume < .01, (label, "support contact has volume overlap", contact_volume)
        distance = part.distance_to(main)
        close(distance, 0.)
        areas = common_face_areas(part, main)
        common_area = max(areas, default=0.)
        assert common_area > .001, (label, "missing common support face", areas)
        contacts[label] = {"distance_mm": distance, "common_face_area_mm2": common_area,
                           "overlap_mm3": contact_volume}
        for other_label, other in baseline.items():
            if other_label == MAIN:
                continue
            baseline_pair_count += 1
            if not boxes_overlap(part, other):
                continue
            legacy_overlap_candidates += 1
            overlap = volume(part & other)
            assert overlap < .01, (label, other_label, "legacy-part interference", overlap)

    joint_pair_clearances = {}
    for first, second in combinations(JOINT_PARTS, 2):
        overlap = volume(full[first] & full[second])
        assert overlap < .01, (first, second, "joint-part interference", overlap)
        gap = full[first].distance_to(full[second])
        assert gap > 0., (first, second, "joint parts touch unexpectedly")
        joint_pair_clearances[f"{first}/{second}"] = gap
    fastener_clearances = {}
    for label in FASTENERS:
        ogive_gap = full[label].distance_to(full[OGIVE])
        liner_gap = full[label].distance_to(full["main_joint_liner_1"])
        assert ogive_gap > 0., (label, "ogive clearance")
        assert liner_gap > 0., \
            (label, "liner clearance")
        fastener_clearances[label] = {"ogive_mm": ogive_gap, "liner_mm": liner_gap}
    liner_ogive_gap = full["main_joint_liner_1"].distance_to(full[OGIVE])
    assert liner_ogive_gap > 0., ("liner/ogive clearance", liner_ogive_gap)
    close(liner_ogive_gap, .1, .01)

    # Screw profile/countersink fit, translated R13 geometry, and real slots.
    from halberd_r13_shapes import panel_parts
    r13_fastener = panel_parts()[2]
    stem_radius = 1.3
    bore_radius = 1.36
    head_top_radius = 1.78
    countersink_start_radius = 1.36
    countersink_slope = .76 / .75
    countersink_radius_at_head = countersink_start_radius + countersink_slope * .55
    profile_clearances = {
        "stem_radial_mm": bore_radius - stem_radius,
        "head_top_radial_mm": countersink_radius_at_head - head_top_radius,
        "countersink_opening_radius_at_top_mm": countersink_start_radius + countersink_slope * 1.2,
        "countersink_outer_radial_extent_mm": 94.1 + 1.2,
        "skin_radius_at_x1078_mm": skin_radii,
    }
    assert profile_clearances["stem_radial_mm"] > 0.
    assert profile_clearances["head_top_radial_mm"] > 0.
    assert profile_clearances["countersink_outer_radial_extent_mm"] > skin_max
    for label, clock in zip(FASTENERS, CLOCKS):
        screw = full[label]
        local_screw = screw.rotate(bd.Axis.X, clock)
        close(local_screw.bounding_box().min.Z, 93.5)
        close(local_screw.bounding_box().max.Z, 94.65)
        restored = local_screw.moved(bd.Location((-1446., 0., 5.)))
        identical(restored, r13_fastener)
        close(screw.center(bd.CenterOf.MASS).X, 1078.)
        center = screw.center(bd.CenterOf.MASS)
        close(math.degrees(math.atan2(center.Y, center.Z)) % 360., clock, .002)
        assert volume(screw - fastener_seat(clock)) < .01, (label, "does not fit countersink")
        solid = screw.solids()[0]
        assert not solid.is_inside(radial_point(1078., 94.55, clock)), (label, "missing slot")
        assert solid.is_inside(radial_point(1078.65, 94.55, clock)), (label, "missing head material")

    # Focus must be the exact full artifact clipped to the stated box.
    clip = bd.Box(160., 240., 240.).translate((1085., 0., 0.))
    for label in FOCUS_LABELS:
        identical(focused[label], full[label] & clip)
        assert tuple(focused[label].color) == tuple(full[label].color), label

    # R15 axial extent and existing intake channels remain unchanged/open.
    close(full_scene.roots[0].shape().bounding_box().size.X, 3370.)
    for i in range(1, 5):
        floor = full[f"main_intake_dark_floor_{i}"]
        back = max(vertex.X for vertex in floor.vertices())
        channel_shapes = [main, full[f"main_intake_dark_recess_{i}"], floor]
        for x in (back + .1, -300., -100., 100., 400., 560.):
            angle = 45. + 90. * (i - 1)
            point = (x, 120. * math.sin(math.radians(angle)),
                     120. * math.cos(math.radians(angle)))
            assert not any(shape.solids()[0].is_inside(point) for shape in channel_shapes), \
                (i, x, "intake channel blocked")

    check_materials(full_scene, full_sidecar, baseline_scene, baseline_sidecar,
                    focus_sidecar, focus_scene)
    check_materials(separated_scene, separated_sidecar, baseline_scene, baseline_sidecar,
                    focus_sidecar, focus_scene)
    reference = check_reference_crop()

    report = {
        "ok": True,
        "baseline_r15_hash": baseline_scene.document_hash,
        "full_hash": full_scene.document_hash,
        "separated_hash": separated_scene.document_hash,
        "focus_hash": focus_scene.document_hash,
        "parts_per_full_state": 44,
        "unchanged_non_main_r15_parts": 38,
        "focus_parts": 7,
        "saved_geometry_placements_validated": len(full_rows) + len(separated_rows) + len(focus_rows),
        "main_body_volume_removed_mm3": volume(removed),
        "annular_cut_volume_mm3": volume(ring_removed),
        "seat_cuts": seat_bounds,
        "actual_r15_skin_radius_samples_mm": skin_radii,
        "countersink_fit": profile_clearances,
        "liner_bounds_mm": [liner_bounds.min.X, liner_bounds.max.X,
                             liner_bounds.max.Y, liner_bounds.max.Z],
        "liner_axial_gaps_mm": liner_axial_gaps,
        "body_support_contacts": contacts,
        "new_to_baseline_nonbody_pairs_checked": baseline_pair_count,
        "new_to_baseline_overlap_candidates_boolean_checked": legacy_overlap_candidates,
        "new_joint_pair_clearances_mm": joint_pair_clearances,
        "fastener_clearances_mm": fastener_clearances,
        "liner_ogive_gap_mm": liner_ogive_gap,
        "material_assignments_full": len(full_sidecar["appearance"]["assignments"]),
        "material_assignments_focus": len(focus_sidecar["appearance"]["assignments"]),
        "reference_crop": reference,
        "total_length_mm": full_scene.roots[0].shape().bounding_box().size.X,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ("actual_r15_skin_radius_samples_mm", "body_support_contacts")},
                     indent=2))
    print("PASS: exact R15 preservation, localized joint cuts, support contacts, clearances,",
          "intake channels, materials, focus crop, reference crop, and 95 saved placements.")


if __name__ == "__main__":
    if "--preflight" in sys.argv:
        preflight()
    else:
        run_full()
