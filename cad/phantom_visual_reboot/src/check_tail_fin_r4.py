"""Saved-artifact and sampled-motion checks for the four-station Tail R4 gate.

All compared CAD inputs are saved STEP files.  The four recess cutter sets are
restated here from the approved R3 dimensions, rather than imported from either
tail-fin generator.  The A5 motion helper is used only to reconstruct the
main-wing poses from its saved Stowed STEP.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import sys
import traceback
from pathlib import Path

import build123d as bd
from cadgen import read_scene
from cadgen.geometry import closest_points, overlap_volume


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reviews" / "tail_fin_r4_checks.json"
STATES = ("Stowed", "Midfold", "Deployed")
FRACTIONS = {"Stowed": 0.0, "Midfold": 0.5, "Deployed": 1.0}
EARLY_FRACTIONS = (0.001, 0.002, 0.005, 0.01, 0.02)
FOLD_SAMPLES = tuple(sorted(set(i / 60.0 for i in range(61)) | set(EARLY_FRACTIONS)))

BODY = "RDM9_R7_symmetric_body_20mm_wedge_R4"
A5_LABELS = (
    BODY, "port_carriage", "port_fixed_root", "port_front", "port_join", "port_rear",
    "starboard_carriage", "starboard_fixed_root", "starboard_front", "starboard_join",
    "starboard_rear", "supported_housing", "top_cover",
)
NONBODY_A5 = tuple(label for label in A5_LABELS if label != BODY)
R3_TAIL_LABELS = (
    "tail_r1_fin_root", "tail_r1_fixed_knuckle_aft",
    "tail_r1_fixed_knuckle_forward", "tail_r1_throughpin",
)
TAIL_SUFFIXES = ("fin_root", "fixed_knuckle_aft", "fixed_knuckle_forward", "throughpin")
STATIONS = (
    ("upper_starboard", 0.0),
    ("upper_port", 90.0),
    ("lower_port", 180.0),
    ("lower_starboard", 270.0),
)
TAIL_LABELS = tuple(f"tail_r4_{station}_{suffix}" for station, _ in STATIONS for suffix in TAIL_SUFFIXES)
EXPECTED_LABELS = (*A5_LABELS, *TAIL_LABELS)

A5_PATHS = {state: ROOT / "STEP" / f"O_Interleaved_A5_{state}.step" for state in STATES}
R3_PATHS = {state: ROOT / "STEP" / f"Q_Tail_R3_Recessed_{state}.step" for state in STATES}
R4_PATHS = {state: ROOT / "STEP" / f"Q_Tail_R4_Four_{state}.step" for state in STATES}
R4_BODY_PATH = ROOT / "STEP" / "Q_Tail_R4_Four_Body_Pocket.step"

HINGE_Y = 82.0
HINGE_Z = 83.0
ROOT_X = (-1325.0, -1085.0)
FOLD_ANGLE_DEG = -135.0
POCKET_OFFSET = 0.3
BODY_POCKET_FLOOR_Z = 82.7
HINGE_RELIEF_FLOOR_Z = 79.7
BODY_X_EXPECTED = (-1400.0, 1400.0)
BODY_X_TOL_MM = 1.0e-6
BOOL_IDENTITY_TOL_MM3 = 0.01
OVERLAP_TOL_MM3 = 0.001
CONTACT_EPS_MM3 = 1.0e-5
MOVING_CLEARANCE_MIN_MM = 0.2
STOWED_RADIUS_LIMIT_MM = 125.0
PIN_RADIUS_MM = 1.25
FIN_BORE_RADIUS_MM = 1.5
PIN_BORE_GAP_MM = FIN_BORE_RADIUS_MM - PIN_RADIUS_MM


def fail(report, check, **details):
    report["failures"].append({"check": check, **details})


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


def symdiff_volume(first, second):
    return volume(first - second) + volume(second - first)


def bounds(shape):
    box = shape.bounding_box(optimal=False)
    return {
        "x": [float(box.min.X), float(box.max.X)],
        "y": [float(box.min.Y), float(box.max.Y)],
        "z": [float(box.min.Z), float(box.max.Z)],
    }


def bbox_gap(first, second):
    a, b = bounds(first), bounds(second)
    gaps = [max(0.0, a[axis][0] - b[axis][1], b[axis][0] - a[axis][1])
            for axis in ("x", "y", "z")]
    return math.sqrt(sum(gap * gap for gap in gaps))


def topology(shape):
    solids = list(shape.solids())
    volumes = [float(solid.volume) for solid in solids]
    return {
        "valid": bool(shape.is_valid),
        "solid_count": len(solids),
        "positive_volumes_mm3": volumes,
        "pass": bool(shape.is_valid and len(solids) == 1 and volumes and all(v > 0.0 for v in volumes)),
    }


def flatten_step(path, standalone=False):
    if standalone:
        imported = bd.import_step(str(path))
        leaves = []

        def visit(node):
            children = list(getattr(node, "children", ()) or ())
            if children:
                for child in children:
                    visit(child)
            else:
                leaves.append(node)

        visit(imported)
        parts = {}
        for leaf in leaves:
            label = str(leaf.label)
            if label in parts:
                raise RuntimeError(f"Duplicate STEP labels in {path}: {label!r}")
            solids = list(leaf.solids())
            parts[label] = solids[0] if len(solids) == 1 else leaf
        return parts

    scene = read_scene(str(path))
    parts = {}
    duplicates = []
    for occurrence in scene.leaves():
        label = str(occurrence.label)
        if label in parts:
            duplicates.append(label)
        shape = occurrence.shape()
        solids = list(shape.solids())
        parts[label] = solids[0] if len(solids) == 1 else shape
        if len(solids) == 1:
            parts[label].label = label
    if duplicates:
        raise RuntimeError(f"Duplicate STEP labels in {path}: {duplicates}")
    return parts


def read_inventory(path, expected, report, key, standalone_alias=None):
    if not path.is_file():
        fail(report, "required_saved_STEP_missing", artifact=key, path=str(path))
        return {}
    try:
        parts = flatten_step(path, standalone=bool(standalone_alias))
        document_labels = sorted(parts)
        # The only accepted STEP-stem alias is the isolated singleton body.
        if standalone_alias and set(parts) == {standalone_alias}:
            parts = {BODY: parts[standalone_alias]}
        missing = sorted(set(expected) - set(parts))
        extra = sorted(set(parts) - set(expected))
        shape_records = {label: topology(shape) for label, shape in parts.items()}
        report["saved_artifacts"][key] = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "document_labels": document_labels,
            "labels": sorted(parts),
            "part_count": len(parts),
            "expected_part_count": len(expected),
            "missing_labels": missing,
            "unexpected_labels": extra,
            "topology": shape_records,
        }
        if missing or extra or len(parts) != len(expected):
            fail(report, "saved_STEP_inventory", artifact=key, missing_labels=missing,
                 unexpected_labels=extra, actual_count=len(parts), expected_count=len(expected))
        for label, metrics in shape_records.items():
            if not metrics["pass"]:
                fail(report, "saved_component_not_single_valid_positive_solid",
                     artifact=key, label=label, metrics=metrics)
        return parts
    except Exception as exc:
        fail(report, "saved_STEP_import", artifact=key, path=str(path), error=repr(exc),
             traceback=traceback.format_exc())
        return {}


def _cylinder_x(radius, x0, x1, y, z):
    return bd.Cylinder(radius, x1 - x0,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER)) \
        .rotate(bd.Axis.Y, 90.0).translate(((x0 + x1) / 2.0, y, z))


def independent_pocket_cutters():
    """Independently restate the R3 broad pocket and coaxial hinge reliefs."""
    outline = bd.Wire.make_polygon(
        [(-1325.0, 82.0, 0.0), (-1085.0, 82.0, 0.0),
         (-1180.0, -28.0, 0.0), (-1280.0, -28.0, 0.0)],
        close=True,
    )
    expanded = outline.offset_2d(POCKET_OFFSET, kind=bd.Kind.ARC,
                                 side=bd.Side.BOTH, closed=True)
    broad = bd.extrude(bd.Face(expanded), amount=100.0 - BODY_POCKET_FLOOR_Z,
                       dir=(0, 0, 1)).translate((0, 0, BODY_POCKET_FLOOR_Z))
    return [
        broad,
        _cylinder_x(3.3, -1325.3, -1084.7, HINGE_Y, HINGE_Z),
        _cylinder_x(1.55, -1335.6, -1074.4, HINGE_Y, HINGE_Z),
        _cylinder_x(2.8, -1336.3, -1335.0, HINGE_Y, HINGE_Z),
        _cylinder_x(2.8, -1075.0, -1073.7, HINGE_Y, HINGE_Z),
    ]


def union(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result + shape
    return result.clean()


def rotate_x(shape, angle):
    return shape.rotate(bd.Axis((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)), angle)


def rotated_cutter_union(cutters):
    return union([rotate_x(cutter, angle) for _, angle in STATIONS for cutter in cutters])


def radial_box_bound(shape):
    b = bounds(shape)
    return max(math.hypot(y, z) for y in b["y"] for z in b["z"])


def exact_minimum(pairs):
    """Exact nearest pair, with only conservative disjoint-AABB pruning."""
    candidates = sorted((bbox_gap(a, b), name, a, b) for name, a, b in pairs)
    best = math.inf
    witness = None
    tested = 0
    for lower, name, first, second in candidates:
        if lower > best:
            continue
        distance = float(closest_points(first, second).distance)
        tested += 1
        if distance < best:
            best, witness = distance, name
    return {
        "minimum_clearance_mm": None if math.isinf(best) else best,
        "witness_pair": witness,
        "exact_pairs_tested": tested,
        "AABB_pairs_pruned": len(candidates) - tested,
    }


def station_tail_labels(station):
    return tuple(f"tail_r4_{station}_{suffix}" for suffix in TAIL_SUFFIXES)


def station_for_tail_label(label):
    for station, _ in STATIONS:
        if label.startswith(f"tail_r4_{station}_"):
            return station
    return None


def is_authorized_attachment(a, b):
    pair = frozenset((a, b))
    for station, _ in STATIONS:
        for suffix in ("fixed_knuckle_aft", "fixed_knuckle_forward"):
            if pair == frozenset((f"tail_r4_{station}_{suffix}", BODY)):
                return True
    return pair in {
        frozenset(("supported_housing", "starboard_fixed_root")),
        frozenset(("supported_housing", "port_fixed_root")),
    }


def main():
    report = {
        "gate": "TailR4_saved_geometry_and_sampled_motion",
        "units": "mm",
        "scope": (
            "Four saved R4 assemblies plus isolated body; saved A5/R3 identities; "
            "independent four-station body cuts; 66 synchronous sampled poses. "
            "No model rebuild, rendering, continuous sweep proof, or visual approval. "
            "The existing immutable A5 continuous-pin proof is inherited, not rerun; "
            "cross-station fin pairs are explicitly checked here."
        ),
        "thresholds": {
            "saved_boolean_identity_mm3_exclusive": BOOL_IDENTITY_TOL_MM3,
            "body_outside_cut_difference_mm3_exclusive": BOOL_IDENTITY_TOL_MM3,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "moving_part_minimum_clearance_mm_exclusive": MOVING_CLEARANCE_MIN_MM,
            "fixed_mount_body_positive_overlap_mm3_exclusive": CONTACT_EPS_MM3,
            "body_outer_X_endpoint_tolerance_mm": BODY_X_TOL_MM,
            "stowed_all_part_conservative_YZ_radius_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
            "fold_axis_local_point_yz_mm": [HINGE_Y, HINGE_Z],
            "fold_angle_deg": FOLD_ANGLE_DEG,
            "fold_samples": list(FOLD_SAMPLES),
            "tail_pin_radius_mm": PIN_RADIUS_MM,
            "saved_fin_bore_radius_mm": FIN_BORE_RADIUS_MM,
            "nominal_pin_to_fin_bore_radial_gap_mm": PIN_BORE_GAP_MM,
        },
        "station_angles_global_X_deg": {name: angle for name, angle in STATIONS},
        "saved_artifacts": {},
        "checks": {},
        "failures": [],
    }

    a5, r3, r4 = {}, {}, {}
    for state in STATES:
        a5[state] = read_inventory(A5_PATHS[state], A5_LABELS, report, f"A5_{state}")
        r3[state] = read_inventory(R3_PATHS[state], (*A5_LABELS, *R3_TAIL_LABELS), report,
                                   f"R3_{state}")
        r4[state] = read_inventory(R4_PATHS[state], EXPECTED_LABELS, report, f"R4_{state}")
    r4_body_only = read_inventory(
        R4_BODY_PATH, (BODY,), report, "R4_Body_Pocket",
        standalone_alias="Q_Tail_R4_Four_Body_Pocket",
    )

    # The 12 unmodified A5 components are exact saved-state counterparts.
    a5_identity = {}
    for state in STATES:
        row = {}
        if all(label in a5[state] and label in r4[state] for label in NONBODY_A5):
            for label in NONBODY_A5:
                try:
                    row[label] = symdiff_volume(r4[state][label], a5[state][label])
                except Exception as exc:
                    fail(report, "nonbody_A5_boolean_identity_error", state=state,
                         label=label, error=repr(exc))
        missing = sorted(set(NONBODY_A5) - set(row))
        passed = not missing and all(value < BOOL_IDENTITY_TOL_MM3 for value in row.values())
        a5_identity[state] = {
            "compared_count": len(row), "expected_count": 12,
            "symmetric_difference_mm3_by_label": row,
            "missing_comparisons": missing,
            "pass": passed,
        }
        if missing:
            fail(report, "nonbody_A5_identity_coverage", state=state, missing=missing)
        for label, delta in row.items():
            if delta >= BOOL_IDENTITY_TOL_MM3:
                fail(report, "nonbody_A5_component_changed", state=state, label=label,
                     symmetric_difference_mm3=delta)
    report["checks"]["unchanged_nonbody_A5_components"] = a5_identity

    # Compare every propagated R4 tail part to the matching saved R3 state,
    # transformed by the station map; no generator factory is used as evidence.
    r3_rotation = {}
    r3_comparisons = 0
    for state in STATES:
        rows = {}
        for station, angle in STATIONS:
            for old_label, suffix in zip(R3_TAIL_LABELS, TAIL_SUFFIXES):
                new_label = f"tail_r4_{station}_{suffix}"
                if old_label not in r3[state] or new_label not in r4[state]:
                    continue
                try:
                    expected = rotate_x(r3[state][old_label], angle)
                    delta = symdiff_volume(r4[state][new_label], expected)
                    rows[new_label] = {
                        "source_R3_label": old_label,
                        "station_angle_global_X_deg": angle,
                        "symmetric_difference_mm3": delta,
                        "pass": delta < BOOL_IDENTITY_TOL_MM3,
                    }
                    r3_comparisons += 1
                    if delta >= BOOL_IDENTITY_TOL_MM3:
                        fail(report, "R4_tail_not_rotated_saved_R3_counterpart", state=state,
                             label=new_label, source_label=old_label,
                             symmetric_difference_mm3=delta)
                except Exception as exc:
                    fail(report, "saved_R3_tail_boolean_comparison_error", state=state,
                         label=new_label, source_label=old_label, error=repr(exc))
        r3_rotation[state] = {
            "compared_count": len(rows), "expected_count": 16,
            "maximum_symmetric_difference_mm3": max(
                (row["symmetric_difference_mm3"] for row in rows.values()), default=None),
            "parts": rows,
            "pass": len(rows) == 16 and all(row["pass"] for row in rows.values()),
        }
        if len(rows) != 16:
            fail(report, "R4_saved_R3_tail_identity_coverage", state=state,
                 expected=16, actual=len(rows))
    report["checks"]["tail_parts_rotated_from_saved_R3"] = r3_rotation

    # Reconstruct four independently rotated cutters; compare body, removed
    # material and unchanged outside-cut volume for all three saved states.
    cutters = independent_pocket_cutters()
    cutter_union = rotated_cutter_union(cutters)
    body_checks = {}
    for state in STATES:
        if BODY not in a5[state] or BODY not in r4[state]:
            continue
        try:
            source = a5[state][BODY]
            saved = r4[state][BODY]
            expected = (source - cutter_union).clean()
            delta = symdiff_volume(saved, expected)
            saved_outside = (saved - cutter_union).clean()
            source_outside = (source - cutter_union).clean()
            outside_delta = symdiff_volume(saved_outside, source_outside)
            removed = (source - saved).clean()
            expected_removed = (source & cutter_union).clean()
            removed_delta = symdiff_volume(removed, expected_removed)
            added_volume = volume(saved - source)
            saved_topology = topology(saved)
            expected_topology = topology(expected)
            body_bounds = bounds(saved)
            x_pass = (abs(body_bounds["x"][0] - BODY_X_EXPECTED[0]) <= BODY_X_TOL_MM
                      and abs(body_bounds["x"][1] - BODY_X_EXPECTED[1]) <= BODY_X_TOL_MM)
            row = {
                "saved_vs_A5_minus_four_independent_cutter_sets_mm3": delta,
                "outside_cut_symmetric_difference_mm3": outside_delta,
                "removed_region_vs_original_intersect_cutters_mm3": removed_delta,
                "added_material_mm3": added_volume,
                "saved_body_topology": saved_topology,
                "independent_expected_body_topology": expected_topology,
                "saved_body_bounds_mm": body_bounds,
                "expected_outer_X_mm": list(BODY_X_EXPECTED),
                "outer_X_pass": x_pass,
                "pass": (delta < BOOL_IDENTITY_TOL_MM3
                         and outside_delta < BOOL_IDENTITY_TOL_MM3
                         and removed_delta < BOOL_IDENTITY_TOL_MM3
                         and added_volume < BOOL_IDENTITY_TOL_MM3
                         and saved_topology["pass"] and expected_topology["pass"] and x_pass),
            }
            body_checks[state] = row
            if not row["pass"]:
                fail(report, "body_not_exactly_A5_minus_four_R3_pocket_sets", state=state, **row)
        except Exception as exc:
            fail(report, "independent_four_pocket_body_boolean_error", state=state,
                 error=repr(exc), traceback=traceback.format_exc())
    report["checks"]["body_exactly_four_rotated_pocket_sets"] = body_checks

    # Isolated body is checked against the independently cut A5 Stowed body
    # and the full R4 Stowed body's saved body; only the known stem alias above
    # is accepted for a singleton STEP.
    isolated_identity = {}
    if BODY in r4_body_only and BODY in a5["Stowed"] and BODY in r4["Stowed"]:
        try:
            expected = (a5["Stowed"][BODY] - cutter_union).clean()
            delta_expected = symdiff_volume(r4_body_only[BODY], expected)
            delta_assembly = symdiff_volume(r4_body_only[BODY], r4["Stowed"][BODY])
            isolated_identity = {
                "isolated_vs_A5_stowed_minus_four_cutters_mm3": delta_expected,
                "isolated_vs_full_R4_stowed_body_mm3": delta_assembly,
                "topology": topology(r4_body_only[BODY]),
                "pass": (delta_expected < BOOL_IDENTITY_TOL_MM3
                         and delta_assembly < BOOL_IDENTITY_TOL_MM3
                         and topology(r4_body_only[BODY])["pass"]),
            }
            if not isolated_identity["pass"]:
                fail(report, "R4_isolated_body_pocket_identity", **isolated_identity)
        except Exception as exc:
            fail(report, "R4_isolated_body_pocket_comparison_error", error=repr(exc),
                 traceback=traceback.format_exc())
    else:
        fail(report, "R4_isolated_body_pocket_comparison_inputs_missing")
    report["checks"]["isolated_body_pocket_identity"] = isolated_identity

    # Measure broad-floor/crown relief depth in each cutter's own rotated frame.
    pocket_station_checks = {}
    if BODY in a5["Stowed"] and BODY in r4["Stowed"]:
        source = a5["Stowed"][BODY]
        saved = r4["Stowed"][BODY]
        broad, hinge_relief = cutters[0], cutters[1]
        for station, angle in STATIONS:
            try:
                source_local = rotate_x(source, -angle)
                saved_local = rotate_x(saved, -angle)
                removed_local = (source_local - saved_local).clean()
                broad_removed = (removed_local & broad).clean()
                relief_removed = (removed_local & hinge_relief).clean()
                broad_before = (source_local & broad).clean()
                probe_center = (-1180.0, 0.0, 85.0)
                probe = bd.Box(0.2, 0.2, 0.2).translate(probe_center)
                probe_before = volume(source_local & probe)
                probe_after = volume(saved_local & probe)
                probe_removed = volume(removed_local & probe)
                face_world = (
                    -1180.0,
                    -86.0 * math.sin(math.radians(angle)),
                    86.0 * math.cos(math.radians(angle)),
                )
                broad_bounds = bounds(broad_removed) if volume(broad_removed) > 0.0 else None
                relief_bounds = bounds(relief_removed) if volume(relief_removed) > 0.0 else None
                floor = broad_bounds["z"][0] if broad_bounds else None
                relief_floor = relief_bounds["z"][0] if relief_bounds else None
                row = {
                    "station_angle_global_X_deg": angle,
                    "flat_fin_outer_face_local_z_mm": 86.0,
                    "flat_face_probe_world_xyz_mm": list(face_world),
                    "expected_global_body_face_coordinate_at_probe_mm": (
                        "Y=-86" if angle == 90.0 else "Y=+86" if angle == 270.0
                        else "Z=+86" if angle == 0.0 else "Z=-86"),
                    "independent_broad_pocket_floor_local_z_mm": BODY_POCKET_FLOOR_Z,
                    "measured_removed_broad_floor_local_z_mm": floor,
                    "flat_face_to_broad_floor_depth_mm": 86.0 - BODY_POCKET_FLOOR_Z,
                    "broad_removed_volume_mm3": volume(broad_removed),
                    "source_body_broad_cutter_intersection_volume_mm3": volume(broad_before),
                    "hinge_relief_expected_local_floor_z_mm": HINGE_RELIEF_FLOOR_Z,
                    "measured_removed_hinge_relief_floor_local_z_mm": relief_floor,
                    "hinge_relief_removed_volume_mm3": volume(relief_removed),
                    "planform_probe_center_local_xyz_mm": list(probe_center),
                    "planform_probe_source_material_mm3": probe_before,
                    "planform_probe_saved_body_material_mm3": probe_after,
                    "planform_probe_removed_material_mm3": probe_removed,
                }
                fin_label = f"tail_r4_{station}_fin_root"
                if fin_label in r4["Stowed"]:
                    fin_local = rotate_x(r4["Stowed"][fin_label], -angle)
                    crown = _cylinder_x(3.0, *ROOT_X, HINGE_Y, HINGE_Z)
                    crown_in_fin = (fin_local & crown).clean()
                    fin_zmax = bounds(fin_local)["z"][1]
                    crown_zmax = bounds(crown_in_fin)["z"][1] if volume(crown_in_fin) > 0.0 else None
                    row.update({
                        "saved_fin_local_outer_flat_face_z_mm": fin_zmax,
                        "saved_hinge_crown_intersection_volume_mm3": volume(crown_in_fin),
                        "saved_hinge_crown_local_top_z_mm": crown_zmax,
                        "hinge_crown_flush_to_flat_face_mm": (
                            None if crown_zmax is None else abs(crown_zmax - fin_zmax)),
                    })
                face_probe_pass = (probe_before > 0.0 and probe_after < CONTACT_EPS_MM3
                                   and abs(probe_before - probe_removed) < BOOL_IDENTITY_TOL_MM3)
                floor_pass = (floor is not None and abs(floor - BODY_POCKET_FLOOR_Z) <= BODY_X_TOL_MM
                              and relief_floor is not None
                              and abs(relief_floor - HINGE_RELIEF_FLOOR_Z) <= BODY_X_TOL_MM)
                crown_pass = (row.get("saved_hinge_crown_local_top_z_mm") is not None
                              and row.get("saved_hinge_crown_intersection_volume_mm3", 0.0) > 0.0
                              and row.get("hinge_crown_flush_to_flat_face_mm", math.inf) <= BODY_X_TOL_MM)
                row["pass"] = (volume(broad_removed) > 0.0 and volume(broad_before) > 0.0
                               and volume(relief_removed) > 0.0 and face_probe_pass
                               and floor_pass and crown_pass)
                pocket_station_checks[station] = row
                if not row["pass"]:
                    fail(report, "rotated_pocket_depth_or_flush_face", station=station, **row)
            except Exception as exc:
                fail(report, "rotated_pocket_measurement_error", station=station, error=repr(exc),
                     traceback=traceback.format_exc())
    else:
        fail(report, "rotated_pocket_measurement_inputs_missing")
    report["checks"]["four_rotated_pocket_depths_and_flush_faces"] = pocket_station_checks

    # Positive attachment is measured for all eight fixed mounts; pins and fins
    # have no body exemption and remain in the complete pairwise overlap check.
    mount_contacts = {}
    for state in STATES:
        if BODY not in r4[state]:
            continue
        body = r4[state][BODY]
        rows = {}
        for station, _ in STATIONS:
            for suffix in ("fixed_knuckle_aft", "fixed_knuckle_forward"):
                label = f"tail_r4_{station}_{suffix}"
                if label not in r4[state]:
                    continue
                try:
                    amount = float(overlap_volume(r4[state][label], body))
                    rows[label] = {"mount_body_overlap_mm3": amount,
                                   "positive_contact": amount > CONTACT_EPS_MM3}
                    if amount <= CONTACT_EPS_MM3:
                        fail(report, "fixed_mount_body_contact_not_positive", state=state,
                             label=label, overlap_mm3=amount, minimum_mm3_exclusive=CONTACT_EPS_MM3)
                except Exception as exc:
                    fail(report, "fixed_mount_body_contact_measurement_error", state=state,
                         label=label, error=repr(exc))
        mount_contacts[state] = {
            "compared_count": len(rows), "expected_count": 8,
            "contacts": rows,
            "pass": len(rows) == 8 and all(row["positive_contact"] for row in rows.values()),
        }
        if len(rows) != 8:
            fail(report, "fixed_mount_body_contact_coverage", state=state, expected=8, actual=len(rows))
    report["checks"]["eight_positive_fixed_mount_body_contacts"] = mount_contacts

    # Global stowed conservative radial envelope and strict body X end points.
    stowed_bounds = {}
    if all(label in r4["Stowed"] for label in EXPECTED_LABELS):
        per_part_radius = {label: radial_box_bound(r4["Stowed"][label]) for label in EXPECTED_LABELS}
        witness = max(per_part_radius, key=per_part_radius.get)
        max_radius = per_part_radius[witness]
        per_part_x = {label: bounds(r4["Stowed"][label])["x"] for label in EXPECTED_LABELS}
        x_outliers = {
            label: interval for label, interval in per_part_x.items()
            if interval[0] < BODY_X_EXPECTED[0] - BODY_X_TOL_MM
            or interval[1] > BODY_X_EXPECTED[1] + BODY_X_TOL_MM
        }
        body_box = bounds(r4["Stowed"][BODY])
        x_pass = (abs(body_box["x"][0] - BODY_X_EXPECTED[0]) <= BODY_X_TOL_MM
                  and abs(body_box["x"][1] - BODY_X_EXPECTED[1]) <= BODY_X_TOL_MM
                  and not x_outliers)
        radius_pass = max_radius < STOWED_RADIUS_LIMIT_MM
        stowed_bounds = {
            "part_count": len(per_part_radius),
            "conservative_YZ_bbox_corner_radius_mm_by_part": per_part_radius,
            "maximum_conservative_radius_mm": max_radius,
            "radius_witness": witness,
            "radius_limit_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
            "X_bounds_mm_by_part": per_part_x,
            "X_out_of_body_envelope_parts": x_outliers,
            "body_X_bounds_mm": body_box["x"],
            "expected_body_X_bounds_mm": list(BODY_X_EXPECTED),
            "body_X_tolerance_mm": BODY_X_TOL_MM,
            "body_X_pass": x_pass,
            "pass": radius_pass and x_pass,
        }
        if not radius_pass:
            fail(report, "global_stowed_radius_not_below_125_mm", measured_mm=max_radius,
                 witness=witness, limit_mm=STOWED_RADIUS_LIMIT_MM)
        if not x_pass:
            fail(report, "stowed_body_outer_X_not_within_1e_6_mm", actual=body_box["x"],
                 expected=list(BODY_X_EXPECTED), tolerance_mm=BODY_X_TOL_MM)
    else:
        fail(report, "global_stowed_envelope_inputs_missing")
    report["checks"]["global_stowed_radius_and_body_X"] = stowed_bounds

    # Saved Midfold/Deployed files must be rigid reconstructions of saved R4
    # Stowed: use the saved-A5 pose helper and rotate each saved fin at its own
    # station hinge axis; pins and mounts remain fixed in their frames.
    motion_helper_errors = []
    pose_identity = {}
    motion_samples = []
    min_moving_clearance = {"minimum_clearance_mm": None, "witness_pair": None, "fraction": None}
    min_fin_fin = {"minimum_clearance_mm": None, "witness_pair": None, "fraction": None}
    min_pin_fin = {"minimum_clearance_mm": None, "witness_pair": None, "fraction": None}
    max_overlap = {"overlap_mm3": 0.0, "fraction": None, "pair": None}
    try:
        sys.path.insert(0, str(ROOT / "src"))
        sys.dont_write_bytecode = True
        import check_interleaved_a5 as a5check

        a5_stowed = a5["Stowed"]
        needed_panels = set(a5check.PANELS) | set(a5check.SUPPORTS)
        missing = sorted(needed_panels - set(a5_stowed))
        if missing:
            raise RuntimeError(f"Saved A5 Stowed lacks motion-helper inputs: {missing}")
        canonical = {
            label: a5check.panel_canonical(
                a5_stowed[label], *label.split("_"), a5check.CUMULATIVE_A2_DROP_MM)
            for label in a5check.PANELS
        }
        r4_stowed = r4["Stowed"]
        station_axis_points = {
            station: rotate_x(bd.Vertex(0.0, HINGE_Y, HINGE_Z), angle).center()
            for station, angle in STATIONS
        }

        # Check all 29 saved leaves at all three named states against the saved
        # Stowed pose reconstruction; body remains invariant.
        for state in STATES:
            if not all(label in r4_stowed and label in r4[state] for label in EXPECTED_LABELS):
                continue
            fraction = FRACTIONS[state]
            expected = a5check.move_saved_stowed(
                a5_stowed, fraction, canonical, a5check.CUMULATIVE_A2_DROP_MM)
            expected[BODY] = r4_stowed[BODY]
            for station, _ in STATIONS:
                for suffix in TAIL_SUFFIXES:
                    label = f"tail_r4_{station}_{suffix}"
                    moving = r4_stowed[label]
                    if suffix == "fin_root" and fraction:
                        point = station_axis_points[station]
                        moving = moving.rotate(
                            bd.Axis((point.X, point.Y, point.Z), (1.0, 0.0, 0.0)),
                            FOLD_ANGLE_DEG * fraction,
                        )
                    expected[label] = moving
            row = {}
            for label in EXPECTED_LABELS:
                try:
                    delta = symdiff_volume(r4[state][label], expected[label])
                    row[label] = delta
                    if delta >= BOOL_IDENTITY_TOL_MM3:
                        fail(report, "saved_R4_state_not_rigid_stowed_reconstruction",
                             state=state, label=label, fraction=fraction,
                             symmetric_difference_mm3=delta)
                except Exception as exc:
                    fail(report, "saved_R4_pose_boolean_comparison_error", state=state,
                         label=label, error=repr(exc))
            pose_identity[state] = {
                "fraction": fraction,
                "compared_count": len(row),
                "expected_count": 29,
                "maximum_symmetric_difference_mm3": max(row.values(), default=None),
                "symmetric_difference_mm3_by_label": row,
                "pass": len(row) == 29 and all(delta < BOOL_IDENTITY_TOL_MM3 for delta in row.values()),
            }
            if len(row) != 29:
                fail(report, "saved_R4_pose_identity_coverage", state=state, expected=29,
                     actual=len(row))

        # Synchronous 66-sample motion; the saved A5 helper moves the wings and
        # the four R4 fins move around transformed local X axes. All other tail
        # components remain fixed. Static AABB separation prunes only proven
        # disjoint pairs; every intersecting pair receives an exact Boolean.
        a5_names = set(A5_LABELS)
        fin_names = {f"tail_r4_{station}_fin_root" for station, _ in STATIONS}
        fixed_tail_names = set(TAIL_LABELS) - fin_names
        authorized = []
        for station, _ in STATIONS:
            authorized.extend((f"tail_r4_{station}_{suffix}", BODY)
                              for suffix in ("fixed_knuckle_aft", "fixed_knuckle_forward"))
        authorized.extend(("supported_housing", "starboard_fixed_root"))
        authorized.extend(("supported_housing", "port_fixed_root"))
        all_pairs_expected = len(EXPECTED_LABELS) * (len(EXPECTED_LABELS) - 1) // 2
        pair_errors = []
        for sample_index, fraction in enumerate(FOLD_SAMPLES):
            posed = a5check.move_saved_stowed(
                a5_stowed, fraction, canonical, a5check.CUMULATIVE_A2_DROP_MM)
            posed[BODY] = r4_stowed[BODY]
            for station, _ in STATIONS:
                point = station_axis_points[station]
                for suffix in TAIL_SUFFIXES:
                    label = f"tail_r4_{station}_{suffix}"
                    part = r4_stowed[label]
                    if suffix == "fin_root" and fraction:
                        part = part.rotate(
                            bd.Axis((point.X, point.Y, point.Z), (1.0, 0.0, 0.0)),
                            FOLD_ANGLE_DEG * fraction,
                        )
                    posed[label] = part

            present = [label for label in EXPECTED_LABELS if label in posed]
            missing_parts = sorted(set(EXPECTED_LABELS) - set(present))
            if missing_parts:
                fail(report, "motion_sample_part_coverage", sample=sample_index,
                     fraction=fraction, missing=missing_parts)
                continue
            overlaps = []
            intersecting_tested = 0
            pruned = 0
            moving_pairs = []
            fin_fin_pairs = []
            pin_fin_pairs = []
            for first_label, second_label in itertools.combinations(present, 2):
                if is_authorized_attachment(first_label, second_label):
                    continue
                first, second = posed[first_label], posed[second_label]
                lower = bbox_gap(first, second)
                if lower > 0.0:
                    pruned += 1
                else:
                    try:
                        amount = float(overlap_volume(first, second))
                        intersecting_tested += 1
                        if amount >= OVERLAP_TOL_MM3:
                            item = {"pair": [first_label, second_label], "overlap_mm3": amount}
                            overlaps.append(item)
                            if amount > max_overlap["overlap_mm3"]:
                                max_overlap = {"overlap_mm3": amount, "fraction": fraction,
                                               "pair": [first_label, second_label]}
                    except Exception as exc:
                        pair_errors.append({"sample": sample_index, "fraction": fraction,
                                            "pair": [first_label, second_label], "error": repr(exc)})
                        fail(report, "motion_pair_overlap_measurement_error", sample=sample_index,
                             fraction=fraction, pair=[first_label, second_label], error=repr(exc))
                if first_label in fin_names or second_label in fin_names:
                    moving_pairs.append((f"{first_label}:{second_label}", first, second))
                    if first_label in fin_names and second_label in fin_names:
                        fin_fin_pairs.append((f"{first_label}:{second_label}", first, second))
                    if ((first_label in fin_names and second_label.endswith("_throughpin"))
                            or (second_label in fin_names and first_label.endswith("_throughpin"))):
                        fin_label = first_label if first_label in fin_names else second_label
                        pin_label = second_label if fin_label == first_label else first_label
                        fin_station = station_for_tail_label(fin_label)
                        pin_station = station_for_tail_label(pin_label)
                        if fin_station == pin_station:
                            pin_fin_pairs.append((f"{fin_label}:{pin_label}", first, second))
            try:
                moving_min = exact_minimum(moving_pairs)
                fin_fin_min = exact_minimum(fin_fin_pairs)
                pin_fin_min = exact_minimum(pin_fin_pairs)
            except Exception as exc:
                moving_min = {"minimum_clearance_mm": None, "witness_pair": None,
                              "error": repr(exc)}
                fin_fin_min = {"minimum_clearance_mm": None, "witness_pair": None,
                               "error": repr(exc)}
                pin_fin_min = {"minimum_clearance_mm": None, "witness_pair": None,
                              "error": repr(exc)}
                fail(report, "motion_exact_clearance_measurement_error", sample=sample_index,
                     fraction=fraction, error=repr(exc), traceback=traceback.format_exc())
            row_pass = (moving_min.get("minimum_clearance_mm") is not None
                        and moving_min["minimum_clearance_mm"] > MOVING_CLEARANCE_MIN_MM
                        and not overlaps and len(moving_pairs) == 106 and len(fin_fin_pairs) == 6
                        and len(pin_fin_pairs) == 4)
            record = {
                "sample": sample_index,
                "fraction": fraction,
                "angle_deg": FOLD_ANGLE_DEG * fraction,
                "part_count": len(present),
                "all_unique_pair_count": all_pairs_expected,
                "authorized_attachment_exemptions": authorized,
                "AABB_disjoint_pair_count_proven": pruned,
                "AABB_intersecting_pairs_exact_overlap_tested": intersecting_tested,
                "moving_part_pair_count": len(moving_pairs),
                "moving_part_minimum_clearance": moving_min,
                "fin_fin_minimum_gap": fin_fin_min,
                "pin_to_fin_bore_minimum_clearance": pin_fin_min,
                "pin_to_fin_bore_nominal_radial_gap_mm": PIN_BORE_GAP_MM,
                "unexpected_overlaps_ge_0_001_mm3": overlaps,
                "pass": row_pass,
            }
            motion_samples.append(record)
            if moving_min.get("minimum_clearance_mm") is not None:
                value = moving_min["minimum_clearance_mm"]
                if (min_moving_clearance["minimum_clearance_mm"] is None
                        or value < min_moving_clearance["minimum_clearance_mm"]):
                    min_moving_clearance = {"minimum_clearance_mm": value,
                                            "witness_pair": moving_min["witness_pair"],
                                            "fraction": fraction}
            if fin_fin_min.get("minimum_clearance_mm") is not None:
                value = fin_fin_min["minimum_clearance_mm"]
                if min_fin_fin["minimum_clearance_mm"] is None or value < min_fin_fin["minimum_clearance_mm"]:
                    min_fin_fin = {"minimum_clearance_mm": value,
                                   "witness_pair": fin_fin_min["witness_pair"],
                                   "fraction": fraction}
            if pin_fin_min.get("minimum_clearance_mm") is not None:
                value = pin_fin_min["minimum_clearance_mm"]
                if min_pin_fin["minimum_clearance_mm"] is None or value < min_pin_fin["minimum_clearance_mm"]:
                    min_pin_fin = {"minimum_clearance_mm": value,
                                   "witness_pair": pin_fin_min["witness_pair"],
                                   "fraction": fraction}
            if not row_pass:
                fail(report, "synchronous_motion_clearance_or_overlap", sample=sample_index,
                     fraction=fraction, moving_minimum=moving_min,
                     unexpected_overlaps=overlaps,
                     moving_pair_count=len(moving_pairs), fin_fin_pair_count=len(fin_fin_pairs),
                     pin_fin_pair_count=len(pin_fin_pairs))
        if pair_errors:
            report["checks"]["motion_pair_measurement_errors"] = pair_errors
    except Exception as exc:
        motion_helper_errors.append({"error": repr(exc), "traceback": traceback.format_exc()})
        fail(report, "saved_A5_motion_helper_or_R4_pose_reconstruction_error",
             error=repr(exc), traceback=traceback.format_exc())

    report["checks"]["saved_R4_pose_identity_from_stowed"] = pose_identity
    motion_summary = {
        "sample_count": len(motion_samples),
        "expected_sample_count": 66,
        "uniform_sample_count": 61,
        "early_fractions": list(EARLY_FRACTIONS),
        "all_29_parts_per_sample": all(row["part_count"] == 29 for row in motion_samples),
        "all_unique_pair_count_per_sample": 406,
        "authorized_attachment_exemptions_count": 10,
        "minimum_moving_part_clearance_mm": min_moving_clearance,
        "minimum_fin_fin_gap_mm": min_fin_fin,
        "minimum_pin_to_fin_bore_clearance_mm": min_pin_fin,
        "nominal_pin_to_fin_bore_radial_gap_mm": PIN_BORE_GAP_MM,
        "maximum_unexpected_overlap": max_overlap,
        "all_samples_pass": len(motion_samples) == 66 and all(row["pass"] for row in motion_samples),
        "continuous_A5_pin_sweep_proof": "inherited from immutable A5 saved checker; not rerun",
        "samples": motion_samples,
    }
    if len(motion_samples) != 66:
        fail(report, "66_sample_motion_coverage", expected=66, actual=len(motion_samples))
    report["checks"]["synchronous_66_sample_motion"] = motion_summary

    report["passed"] = not report["failures"]
    report["summary"] = {
        "passed": report["passed"],
        "failure_count": len(report["failures"]),
        "R4_saved_states_imported": sum(bool(r4[state]) for state in STATES),
        "R4_saved_component_count_each": len(EXPECTED_LABELS),
        "saved_R3_tail_boolean_comparisons": r3_comparisons,
        "nonbody_A5_state_comparisons": sum(row["compared_count"] for row in a5_identity.values()),
        "motion": {
            key: value for key, value in motion_summary.items() if key != "samples"
        },
        "stowed_radius_mm": stowed_bounds.get("maximum_conservative_radius_mm"),
        "pocket_station_count": len(pocket_station_checks),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT_PATH),
        **report["summary"],
        "failed_checks": [item["check"] for item in report["failures"]],
    }, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        failure = {
            "gate": "TailR4_saved_geometry_and_sampled_motion",
            "units": "mm",
            "passed": False,
            "failures": [{"check": "checker_aborted_on_unexpected_exception",
                          "error": repr(exc), "traceback": traceback.format_exc()}],
        }
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(REPORT_PATH), "passed": False,
                          "error": repr(exc)}, indent=2))
        raise SystemExit(2)
