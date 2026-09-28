"""Saved-artifact checks for the R2 half-pop-out ramp-intake gate."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True

import build123d as bd
from cadgen import read_scene
from cadgen.geometry import closest_points, overlap_volume


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reviews" / "ramp_intake_r2_checks.json"
STATES = ("Stowed", "Midfold", "Deployed")
FRACTIONS = {"Stowed": 0.0, "Midfold": 0.5, "Deployed": 1.0}
R1_ANGLE_DEG = 5.0
R2_ANGLE_DEG = 2.497370647093458
HINGE_X = -950.0
HINGE_Z = -83.0
BELLY_Z = -86.0
MOUTH_X = -305.0
BOOL_IDENTITY_TOL_MM3 = 0.01
OVERLAP_TOL_MM3 = 0.001
CONTACT_EPS_MM3 = 1.0e-5
MIN_CLEARANCE_MM = 0.2
STOWED_RADIUS_LIMIT_MM = 125.0
DROP_TOL_MM = 1.0e-5
VERTEX_PICK_TOL_MM = 1.0e-4

R2_PATHS = {state: ROOT / "STEP" / f"R_RampIntake_R2_{state}.step" for state in STATES}
R2_MODULE_PATH = ROOT / "STEP" / "R_RampIntake_R2_Module_Deployed.step"
R1_PATHS = {state: ROOT / "STEP" / f"R_RampIntake_R1_{state}.step" for state in STATES}
R1_MODULE_PATH = ROOT / "STEP" / "R_RampIntake_R1_Module_Deployed.step"
R1_BODY_CAVITY_PATH = ROOT / "STEP" / "R_RampIntake_R1_Body_Cavity.step"
BODY = "RDM9_R7_symmetric_body_20mm_wedge_R4"
RAMP_LABEL = "intake_r1_ramp"
NEW_LABELS = (
    RAMP_LABEL,
    "intake_r1_fixed_mount_negative_y",
    "intake_r1_fixed_mount_positive_y",
    "intake_r1_throughpin",
)
MOUNT_BODY_PAIRS = {
    frozenset((NEW_LABELS[1], BODY)),
    frozenset((NEW_LABELS[2], BODY)),
}


def fail(report, check, **details):
    report["failures"].append({"check": check, **details})


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


def one_solid(shape, description):
    solids = list(shape.solids())
    if len(solids) != 1:
        raise RuntimeError(f"Expected one solid for {description}; found {len(solids)}")
    return solids[0]


def topology(shape):
    solids = list(shape.solids())
    volumes = [float(solid.volume) for solid in solids]
    return {
        "valid": bool(shape.is_valid),
        "solid_count": len(solids),
        "positive_solid_volumes_mm3": volumes,
        "pass": bool(shape.is_valid and len(solids) == 1 and volumes and all(v > 0.0 for v in volumes)),
    }


def load_parts(path):
    scene = read_scene(str(path))
    parts = {}
    duplicates = []
    for occurrence in scene.leaves():
        label = str(occurrence.label)
        if label in parts:
            duplicates.append(label)
        parts[label] = occurrence.shape()
    if duplicates:
        raise RuntimeError(f"Duplicate STEP leaf labels in {path}: {sorted(set(duplicates))}")
    return parts


def inspect_artifact(path, expected_labels, report, key, singleton_alias=None):
    if not path.is_file():
        fail(report, "required_saved_STEP_missing", artifact=key, path=str(path))
        return {}
    try:
        parts = load_parts(path)
        document_labels = sorted(parts)
        if singleton_alias is not None:
            if len(parts) != 1:
                raise RuntimeError(f"Expected one leaf in {path}; found {len(parts)}")
            parts = {singleton_alias: next(iter(parts.values()))}
        missing = sorted(set(expected_labels) - set(parts))
        extra = sorted(set(parts) - set(expected_labels))
        part_topology = {label: topology(shape) for label, shape in parts.items()}
        report["saved_artifacts"][key] = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "document_labels": document_labels,
            "labels": sorted(parts),
            "part_count": len(parts),
            "expected_part_count": len(expected_labels),
            "missing_labels": missing,
            "unexpected_labels": extra,
            "topology": part_topology,
        }
        if missing or extra or len(parts) != len(expected_labels):
            fail(report, "saved_STEP_inventory", artifact=key, missing_labels=missing,
                 unexpected_labels=extra, actual_count=len(parts), expected_count=len(expected_labels))
        for label, metrics in part_topology.items():
            if not metrics["pass"]:
                fail(report, "saved_component_not_single_valid_positive_solid",
                     artifact=key, label=label, topology=metrics)
        return parts
    except Exception as exc:
        fail(report, "saved_STEP_import_or_inventory_error", artifact=key, path=str(path),
             error=repr(exc), traceback=traceback.format_exc())
        return {}


def measure(shape, description):
    return one_solid(shape, description)


def symdiff_volume(first, second):
    return volume(first - second) + volume(second - first)


def compare_geometry(actual, expected, report, check, **details):
    try:
        delta = symdiff_volume(measure(actual, f"actual {check}"), measure(expected, f"expected {check}"))
        passed = delta < BOOL_IDENTITY_TOL_MM3
        row = {**details, "symmetric_difference_mm3": delta,
               "tolerance_mm3_exclusive": BOOL_IDENTITY_TOL_MM3, "pass": passed}
        if not passed:
            fail(report, check, **row)
        return row
    except Exception as exc:
        fail(report, check + "_measurement_error", **details, error=repr(exc),
             traceback=traceback.format_exc())
        return {**details, "pass": False, "error": repr(exc)}


def shape_bounds(shape):
    box = shape.bounding_box(optimal=False)
    return {
        "x": [float(box.min.X), float(box.max.X)],
        "y": [float(box.min.Y), float(box.max.Y)],
        "z": [float(box.min.Z), float(box.max.Z)],
    }


def bbox_gap(first, second):
    a, b = shape_bounds(first), shape_bounds(second)
    gaps = [max(0.0, a[axis][0] - b[axis][1], b[axis][0] - a[axis][1])
            for axis in ("x", "y", "z")]
    return math.sqrt(sum(gap * gap for gap in gaps))


def pair_result(first, second):
    lower = bbox_gap(first, second)
    if lower > MIN_CLEARANCE_MM:
        distance, method, overlap = lower, "disjoint_AABB_lower_bound", 0.0
    else:
        distance = float(closest_points(first, second).distance)
        method = "exact_nearest_points_and_overlap" if lower == 0.0 else "exact_nearest_points"
        overlap = float(overlap_volume(first, second)) if lower == 0.0 else 0.0
    return {
        "clearance_mm": distance,
        "method": method,
        "overlap_mm3": overlap,
        "pass": distance > MIN_CLEARANCE_MM and overlap < OVERLAP_TOL_MM3,
    }


def rotate_ramp(shape, angle_deg):
    return shape.rotate(bd.Axis((HINGE_X, 0.0, HINGE_Z), (0.0, 1.0, 0.0)), angle_deg)


def rotate_point_y(point, angle_deg):
    x, y, z = point
    dx, dz = x - HINGE_X, z - HINGE_Z
    angle = math.radians(angle_deg)
    return (
        HINGE_X + dx * math.cos(angle) + dz * math.sin(angle),
        y,
        HINGE_Z - dx * math.sin(angle) + dz * math.cos(angle),
    )


def nearest_saved_vertex(shape, target):
    points = [vertex.center() for vertex in shape.vertices()]
    if not points:
        raise RuntimeError("Saved ramp has no vertices")
    point = min(points, key=lambda p: math.dist((p.X, p.Y, p.Z), target))
    distance = math.dist((point.X, point.Y, point.Z), target)
    if distance > VERTEX_PICK_TOL_MM:
        raise RuntimeError(f"No saved vertex within {VERTEX_PICK_TOL_MM} mm of {target}; nearest={distance}")
    return {"xyz_mm": [float(point.X), float(point.Y), float(point.Z)], "pick_residual_mm": distance}


def outer_lip_drop(saved_stowed, saved_deployed, angle_deg, description):
    # The saved R1 stowed floor's two lower forward corners are the selected
    # witnesses. Locate the corresponding actual vertices in each saved STEP.
    reference_points = ((-290.0, -64.0, -86.0), (-290.0, 64.0, -86.0))
    stowed_witnesses = [nearest_saved_vertex(saved_stowed, point) for point in reference_points]
    deployed_targets = [rotate_point_y(point, angle_deg) for point in reference_points]
    deployed_witnesses = [nearest_saved_vertex(saved_deployed, point) for point in deployed_targets]
    stowed_z = [row["xyz_mm"][2] for row in stowed_witnesses]
    deployed_z = [row["xyz_mm"][2] for row in deployed_witnesses]
    drops = [a - b for a, b in zip(stowed_z, deployed_z)]
    return {
        "description": description,
        "selected_edge": "saved floor lower forward outer edge; y=+/-64 mm corners",
        "angle_deg_used_for_vertex_correspondence": angle_deg,
        "stowed_saved_vertices": stowed_witnesses,
        "deployed_saved_vertices": deployed_witnesses,
        "per_corner_vertical_drop_mm": drops,
        "measured_mean_vertical_drop_mm": sum(drops) / len(drops),
    }


def check_saved_identity(report, r1_parts, r2_parts, r1_module, r2_module,
                         expected_full_labels):
    nonramp_labels = tuple(label for label in expected_full_labels if label != RAMP_LABEL)
    rows_by_state = {}
    for state in STATES:
        actual, reference = r2_parts.get(state, {}), r1_parts.get(state, {})
        rows = {}
        for label in nonramp_labels:
            if label in actual and label in reference:
                rows[label] = compare_geometry(actual[label], reference[label], report,
                                               "R2_nonramp_part_differs_from_R1_saved_state",
                                               state=state, label=label)
        expected_count = len(nonramp_labels)
        row = {"compared_count": len(rows), "expected_count": expected_count, "parts": rows,
               "pass": len(rows) == expected_count and all(item["pass"] for item in rows.values())}
        rows_by_state[state] = row
        if len(rows) != expected_count:
            fail(report, "R2_nonramp_identity_coverage", state=state,
                 expected=expected_count, actual=len(rows))
    report["checks"]["unchanged_32_nonramp_parts_match_R1"] = rows_by_state

    stowed_rows = {}
    for label in expected_full_labels:
        if label in r2_parts.get("Stowed", {}) and label in r1_parts.get("Stowed", {}):
            stowed_rows[label] = compare_geometry(
                r2_parts["Stowed"][label], r1_parts["Stowed"][label], report,
                "R2_stowed_part_differs_from_R1", state="Stowed", label=label)
    report["checks"]["all_33_stowed_parts_identical_to_R1"] = {
        "compared_count": len(stowed_rows), "expected_count": len(expected_full_labels),
        "parts": stowed_rows,
        "pass": len(stowed_rows) == len(expected_full_labels)
                and all(row["pass"] for row in stowed_rows.values()),
    }
    if len(stowed_rows) != len(expected_full_labels):
        fail(report, "R2_stowed_identity_coverage", expected=len(expected_full_labels),
             actual=len(stowed_rows))

    pose_rows = {}
    for state in STATES:
        fraction = FRACTIONS[state]
        actual = r2_parts.get(state, {}).get(RAMP_LABEL)
        r2_stowed = r2_parts.get("Stowed", {}).get(RAMP_LABEL)
        r1_state = r1_parts.get(state, {}).get(RAMP_LABEL)
        if actual is None or r2_stowed is None or r1_state is None:
            fail(report, "R2_ramp_pose_identity_inputs_missing", state=state)
            pose_rows[state] = {"pass": False, "fraction": fraction}
            continue
        expected_from_r2_stow = rotate_ramp(r2_stowed, R2_ANGLE_DEG * fraction)
        expected_from_r1_pose = rotate_ramp(r1_state, (R2_ANGLE_DEG - R1_ANGLE_DEG) * fraction)
        from_stow = compare_geometry(actual, expected_from_r2_stow, report,
                                     "R2_ramp_not_rotation_of_saved_stowed_ramp",
                                     state=state, fraction=fraction,
                                     rotation_deg=R2_ANGLE_DEG * fraction)
        from_r1 = compare_geometry(actual, expected_from_r1_pose, report,
                                   "R2_ramp_not_R1_saved_pose_minus_angle_delta",
                                   state=state, fraction=fraction,
                                   correction_deg=(R2_ANGLE_DEG - R1_ANGLE_DEG) * fraction)
        pose_rows[state] = {"fraction": fraction, "rotation_deg": R2_ANGLE_DEG * fraction,
                            "from_saved_R2_stowed": from_stow,
                            "from_saved_R1_pose_after_inverse_5deg_correction": from_r1,
                            "pass": from_stow["pass"] and from_r1["pass"]}
    report["checks"]["saved_ramp_pose_identity_two_independent_reconstructions"] = pose_rows

    module_rows = {}
    for label in NEW_LABELS:
        if label in r2_module and label in r2_parts.get("Deployed", {}):
            module_rows[label] = compare_geometry(
                r2_module[label], r2_parts["Deployed"][label], report,
                "R2_module_part_differs_from_full_deployed", state="Deployed", label=label)
        if label != RAMP_LABEL and label in r2_module and label in r1_module:
            compare_geometry(r2_module[label], r1_module[label], report,
                             "R2_module_part_differs_from_R1_module", state="Deployed", label=label)
    report["checks"]["deployed_module_matches_full_and_R1_module"] = {
        "compared_to_R2_full_count": len(module_rows), "expected_count": len(NEW_LABELS),
        "parts": module_rows,
        "pass": len(module_rows) == len(NEW_LABELS) and all(row["pass"] for row in module_rows.values()),
    }
    if len(module_rows) != len(NEW_LABELS):
        fail(report, "R2_module_identity_coverage", expected=len(NEW_LABELS), actual=len(module_rows))

    cavity_rows = {}
    cavity = report["_body_cavity_parts"].get(BODY)
    if cavity is not None:
        for state in STATES:
            body = r2_parts.get(state, {}).get(BODY)
            if body is not None:
                cavity_rows[state] = compare_geometry(
                    body, cavity, report, "R2_body_cavity_differs_from_saved_R1_body_cavity", state=state)
    report["checks"]["body_and_cavity_identity_unchanged"] = {
        "isolated_R1_body_cavity_path": str(R1_BODY_CAVITY_PATH),
        "compared_full_body_states": len(cavity_rows), "expected_count": len(STATES),
        "states": cavity_rows,
        "pass": len(cavity_rows) == len(STATES) and all(row["pass"] for row in cavity_rows.values()),
    }
    if len(cavity_rows) != len(STATES):
        fail(report, "R2_body_cavity_identity_coverage", expected=len(STATES), actual=len(cavity_rows))


def check_lip_drop(report, r1_parts, r2_parts):
    try:
        r1_measure = outer_lip_drop(
            measure(r1_parts["Stowed"][RAMP_LABEL], "R1 saved Stowed ramp"),
            measure(r1_parts["Deployed"][RAMP_LABEL], "R1 saved Deployed ramp"),
            R1_ANGLE_DEG, "R1 saved baseline measured from saved edge vertices")
        r2_measure = outer_lip_drop(
            measure(r2_parts["Stowed"][RAMP_LABEL], "R2 saved Stowed ramp"),
            measure(r2_parts["Deployed"][RAMP_LABEL], "R2 saved Deployed ramp"),
            R2_ANGLE_DEG, "R2 saved result measured from saved edge vertices")
        expected_half = r1_measure["measured_mean_vertical_drop_mm"] / 2.0
        residual = abs(r2_measure["measured_mean_vertical_drop_mm"] - expected_half)
        row = {
            "method": "independently pick corresponding lower forward-edge vertices from saved R1/R2 STEP B-reps; compare actual world-Z differences",
            "required_half_of_saved_R1_drop_mm": expected_half,
            "saved_R1_measurement": r1_measure,
            "saved_R2_measurement": r2_measure,
            "absolute_deviation_from_half_mm": residual,
            "tolerance_mm_inclusive": DROP_TOL_MM,
            "pass": residual <= DROP_TOL_MM,
        }
        report["checks"]["measured_saved_outer_lip_drop_is_half_R1"] = row
        if not row["pass"]:
            fail(report, "saved_R2_outer_lip_drop_not_half_R1", **row)
    except Exception as exc:
        fail(report, "saved_outer_lip_drop_measurement_error", error=repr(exc),
             traceback=traceback.format_exc())
        report["checks"]["measured_saved_outer_lip_drop_is_half_R1"] = {"pass": False, "error": repr(exc)}


def check_stowed_envelope(report, r2_parts, expected_full_labels):
    try:
        parts = r2_parts["Stowed"]
        floor = measure(parts[RAMP_LABEL], "R2 saved stowed ramp")
        floor_min_z = float(floor.bounding_box().min.Z)
        hardware_labels = NEW_LABELS[1:]
        hardware_min_z = {label: float(measure(parts[label], label).bounding_box().min.Z)
                          for label in hardware_labels}
        radii = {}
        for label in expected_full_labels:
            shape = measure(parts[label], f"R2 stowed {label}")
            box = shape.bounding_box(optimal=False)
            radii[label] = max(math.hypot(y, z)
                               for y in (float(box.min.Y), float(box.max.Y))
                               for z in (float(box.min.Z), float(box.max.Z)))
        witness = max(radii, key=radii.get)
        row = {
            "full_stowed_part_count": len(parts),
            "expected_part_count": len(expected_full_labels),
            "floor_tight_min_Z_mm": floor_min_z,
            "belly_Z_mm": BELLY_Z,
            "stowed_floor_flush_error_mm": abs(floor_min_z - BELLY_Z),
            "stowed_floor_flush_tolerance_mm": 1.0e-6,
            "hardware_tight_min_Z_by_part_mm": hardware_min_z,
            "hardware_lowest_Z_mm": min(hardware_min_z.values()),
            "hardware_above_or_on_belly": min(hardware_min_z.values()) >= BELLY_Z,
            "conservative_YZ_AABB_corner_radius_mm_by_part": radii,
            "maximum_conservative_radius_mm": radii[witness],
            "radius_witness": witness,
            "radius_limit_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
            "pass": len(parts) == len(expected_full_labels)
                    and abs(floor_min_z - BELLY_Z) <= 1.0e-6
                    and min(hardware_min_z.values()) >= BELLY_Z
                    and radii[witness] < STOWED_RADIUS_LIMIT_MM,
        }
        report["checks"]["stowed_flush_hardware_and_125mm_envelope"] = row
        if not row["pass"]:
            fail(report, "R2_stowed_floor_hardware_or_125mm_envelope", **row)
    except Exception as exc:
        fail(report, "R2_stowed_envelope_measurement_error", error=repr(exc),
             traceback=traceback.format_exc())


def check_mount_contacts(report, r2_parts):
    rows_by_state = {}
    for state in STATES:
        parts = r2_parts.get(state, {})
        if BODY not in parts or any(label not in parts for label in NEW_LABELS[1:3]):
            fail(report, "R2_fixed_mount_contact_inputs_missing", state=state)
            continue
        body = measure(parts[BODY], f"R2 {state} body")
        contacts = {}
        for label in NEW_LABELS[1:3]:
            amount = float(overlap_volume(measure(parts[label], f"R2 {state} {label}"), body))
            contacts[label] = {"positive_body_contact_overlap_mm3": amount,
                               "minimum_mm3_exclusive": CONTACT_EPS_MM3,
                               "pass": amount > CONTACT_EPS_MM3}
            if not contacts[label]["pass"]:
                fail(report, "R2_fixed_mount_body_contact_not_positive", state=state,
                     label=label, overlap_mm3=amount, minimum_mm3_exclusive=CONTACT_EPS_MM3)
        rows_by_state[state] = {"contacts": contacts, "compared_count": len(contacts),
                                "expected_count": 2, "pass": len(contacts) == 2
                                and all(item["pass"] for item in contacts.values())}
    report["checks"]["only_explicit_fixed_mount_body_contacts"] = {
        "authorized_mount_body_pairs": [sorted(pair) for pair in MOUNT_BODY_PAIRS],
        "states": rows_by_state,
        "pass": len(rows_by_state) == len(STATES) and all(row["pass"] for row in rows_by_state.values()),
    }


def check_mouth(report, r2_parts, expected_full_labels):
    try:
        floor_z = HINGE_Z - (MOUTH_X - HINGE_X) * math.tan(math.radians(R2_ANGLE_DEG))
        z0, z1 = floor_z + 0.3, BELLY_Z - 0.3
        if not z1 > z0:
            raise RuntimeError(f"Nonpositive mouth height: floor={floor_z}, slab=[{z0}, {z1}]")
        mouth = bd.Box(0.2, 124.0, z1 - z0).translate((MOUTH_X, 0.0, (z0 + z1) / 2.0))
        deployed = r2_parts["Deployed"]
        blockers = []
        for label in expected_full_labels:
            if label not in deployed:
                continue
            shape = measure(deployed[label], f"R2 deployed mouth comparison {label}")
            if bbox_gap(mouth, shape) == 0.0:
                amount = float(overlap_volume(measure(mouth, "R2 deployed mouth test slab"), shape))
                if amount >= OVERLAP_TOL_MM3:
                    blockers.append({"label": label, "overlap_mm3": amount})
        row = {
            "test_slab_x_mm": [MOUTH_X - 0.1, MOUTH_X + 0.1],
            "test_y_mm": [-62.0, 62.0],
            "floor_at_test_plane_z_mm": floor_z,
            "test_z_mm": [z0, z1],
            "unobstructed_width_mm": 124.0,
            "unobstructed_height_mm": z1 - z0,
            "tested_final_part_count": len(deployed),
            "expected_final_part_count": len(expected_full_labels),
            "blockers_ge_0_001_mm3": blockers,
            "pass": len(deployed) == len(expected_full_labels) and not blockers,
            "interpretation": "Geometric forward mouth clearance only; no airflow-performance claim.",
        }
        report["checks"]["deployed_forward_mouth_void_clear"] = row
        if not row["pass"]:
            fail(report, "R2_deployed_forward_mouth_obstructed_or_incomplete", **row)
    except Exception as exc:
        fail(report, "R2_mouth_measurement_error", error=repr(exc), traceback=traceback.format_exc())


def check_motion(report, r2_parts, r4_parts, a5_parts, r4check, a5check, basecheck):
    try:
        r4_stowed = r4_parts
        needed = set(a5check.PANELS) | set(a5check.SUPPORTS)
        missing = sorted(needed - set(a5_parts))
        if missing:
            raise RuntimeError(f"Saved A5 Stowed lacks motion helper inputs: {missing}")
        canonical = {
            label: a5check.panel_canonical(
                measure(a5_parts[label], f"saved A5 Stowed {label}"),
                *label.split("_"), a5check.CUMULATIVE_A2_DROP_MM)
            for label in a5check.PANELS
        }
        body = measure(r2_parts["Stowed"][BODY], "R2 saved Stowed body")
        new_stowed = {label: measure(r2_parts["Stowed"][label], f"R2 saved Stowed {label}")
                      for label in NEW_LABELS}
        moving_existing = set(a5check.PANELS) | set(a5check.SUPPORTS)
        moving_existing.update(f"tail_r4_{station}_fin_root" for station, _ in r4check.STATIONS)
        if set(r4_stowed) != set(r4check.EXPECTED_LABELS):
            raise RuntimeError("Saved R4 Stowed inventory is incomplete before motion sampling")

        samples = []
        cached_static_pairs = {}
        minimum = {"clearance_mm": None, "pair": None, "fraction": None, "method": None}
        maximum_overlap = {"overlap_mm3": 0.0, "pair": None, "fraction": None}
        pair_count_expected = len(NEW_LABELS) * len(r4check.EXPECTED_LABELS) + 6
        for sample_index, fraction in enumerate(basecheck.SAMPLES):
            existing = basecheck.reconstruct_existing(
                r4check, a5check, r4_stowed, body, canonical, fraction)
            posed_new = dict(new_stowed)
            posed_new[RAMP_LABEL] = rotate_ramp(new_stowed[RAMP_LABEL], R2_ANGLE_DEG * fraction)
            pair_rows = []
            sample_min = {"clearance_mm": None, "pair": None, "method": None}
            sample_overlap = {"overlap_mm3": 0.0, "pair": None}
            errors = []
            exempt_count = 0
            for new_label, new_shape in posed_new.items():
                for old_label in r4check.EXPECTED_LABELS:
                    pair_key = frozenset((new_label, old_label))
                    if pair_key in MOUNT_BODY_PAIRS:
                        exempt_count += 1
                        continue
                    old_shape = measure(existing[old_label], f"R4 motion {old_label}")
                    stationary = new_label != RAMP_LABEL and old_label not in moving_existing
                    cache_key = (new_label, old_label) if stationary else None
                    try:
                        result = cached_static_pairs.get(cache_key) if cache_key else None
                        if result is None:
                            result = pair_result(measure(new_shape, f"R2 motion {new_label}"), old_shape)
                            if cache_key:
                                cached_static_pairs[cache_key] = result
                        row = {"pair": [new_label, old_label], **result,
                               "result_reused_identical_static_geometry": bool(cache_key and sample_index > 0)}
                        pair_rows.append(row)
                    except Exception as exc:
                        errors.append({"pair": [new_label, old_label], "error": repr(exc)})
                        fail(report, "R2_motion_pair_measurement_error", sample=sample_index,
                             fraction=fraction, pair=[new_label, old_label], error=repr(exc),
                             traceback=traceback.format_exc())
                        continue
                    if sample_min["clearance_mm"] is None or row["clearance_mm"] < sample_min["clearance_mm"]:
                        sample_min = {"clearance_mm": row["clearance_mm"], "pair": row["pair"],
                                      "method": row["method"]}
                    if row["overlap_mm3"] > sample_overlap["overlap_mm3"]:
                        sample_overlap = {"overlap_mm3": row["overlap_mm3"], "pair": row["pair"]}
                    if row["clearance_mm"] < MIN_CLEARANCE_MM or row["overlap_mm3"] >= OVERLAP_TOL_MM3:
                        fail(report, "R2_intake_vs_existing_clearance_or_overlap", sample=sample_index,
                             fraction=fraction, **row, clearance_mm_exclusive=MIN_CLEARANCE_MM,
                             overlap_mm3_exclusive=OVERLAP_TOL_MM3)
            for (first_label, first_shape), (second_label, second_shape) in itertools.combinations(
                    posed_new.items(), 2):
                try:
                    result = pair_result(measure(first_shape, first_label), measure(second_shape, second_label))
                    row = {"pair": [first_label, second_label], **result,
                           "result_reused_identical_static_geometry": False}
                    pair_rows.append(row)
                except Exception as exc:
                    errors.append({"pair": [first_label, second_label], "error": repr(exc)})
                    fail(report, "R2_internal_pair_measurement_error", sample=sample_index,
                         fraction=fraction, pair=[first_label, second_label], error=repr(exc),
                         traceback=traceback.format_exc())
                    continue
                if sample_min["clearance_mm"] is None or row["clearance_mm"] < sample_min["clearance_mm"]:
                    sample_min = {"clearance_mm": row["clearance_mm"], "pair": row["pair"],
                                  "method": row["method"]}
                if row["overlap_mm3"] > sample_overlap["overlap_mm3"]:
                    sample_overlap = {"overlap_mm3": row["overlap_mm3"], "pair": row["pair"]}
                if row["clearance_mm"] < MIN_CLEARANCE_MM or row["overlap_mm3"] >= OVERLAP_TOL_MM3:
                    fail(report, "R2_internal_clearance_or_overlap", sample=sample_index,
                         fraction=fraction, **row, clearance_mm_exclusive=MIN_CLEARANCE_MM,
                         overlap_mm3_exclusive=OVERLAP_TOL_MM3)
            expected_checked = pair_count_expected - len(MOUNT_BODY_PAIRS)
            passed = (len(pair_rows) == expected_checked and exempt_count == len(MOUNT_BODY_PAIRS)
                      and not errors and all(row["clearance_mm"] > MIN_CLEARANCE_MM
                                             and row["overlap_mm3"] < OVERLAP_TOL_MM3
                                             for row in pair_rows))
            samples.append({
                "sample": sample_index, "fraction": fraction,
                "ramp_rotation_deg": R2_ANGLE_DEG * fraction,
                "R4_fin_fold_deg": r4check.FOLD_ANGLE_DEG * fraction,
                "new_part_count": len(posed_new), "existing_part_count": len(existing),
                "all_new_vs_existing_and_internal_pairs_expected": pair_count_expected,
                "nonexempt_pair_count_checked": len(pair_rows),
                "explicit_fixed_mount_body_exemptions": exempt_count,
                "minimum_clearance": sample_min, "maximum_unexpected_overlap": sample_overlap,
                "measurement_error_count": len(errors), "pass": passed,
            })
            if sample_min["clearance_mm"] is not None and (
                    minimum["clearance_mm"] is None or sample_min["clearance_mm"] < minimum["clearance_mm"]):
                minimum = {**sample_min, "fraction": fraction}
            if sample_overlap["overlap_mm3"] > maximum_overlap["overlap_mm3"]:
                maximum_overlap = {**sample_overlap, "fraction": fraction}
            if len(pair_rows) != expected_checked:
                fail(report, "R2_motion_pair_coverage", sample=sample_index,
                     fraction=fraction, expected=expected_checked, actual=len(pair_rows))
        motion_row = {
            "method": "66 saved-input synchronous pose samples: 61 uniform fractions plus five early fractions; inherited R4/A5 reconstruction; R2 ramp rotates saved Stowed ramp by angle*f",
            "sample_count": len(samples), "expected_sample_count": 66,
            "uniform_sample_count": 61, "early_fractions": list(basecheck.EARLY_FRACTIONS),
            "new_part_count": len(NEW_LABELS), "existing_part_count_per_sample": len(r4check.EXPECTED_LABELS),
            "candidate_pair_count_per_sample": pair_count_expected,
            "authorized_exceptions_only": [sorted(pair) for pair in MOUNT_BODY_PAIRS],
            "fixed_mount_body_contacts_checked_separately": True,
            "clearance_mm_exclusive": MIN_CLEARANCE_MM,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "minimum_sampled_clearance": minimum,
            "maximum_unexpected_overlap": maximum_overlap,
            "unique_identical_static_pair_results_cached": len(cached_static_pairs),
            "all_samples_pass": len(samples) == 66 and all(row["pass"] for row in samples),
            "continuous_sweep_claim": "None; specified discrete 66-sample check only.",
            "samples": samples,
        }
        report["checks"]["synchronous_66_sample_R2_clearance_and_overlap"] = motion_row
        if not motion_row["all_samples_pass"]:
            fail(report, "R2_66_sample_motion_clearance_or_overlap_failed",
                 sample_count=len(samples), expected_sample_count=66,
                 all_samples_pass=motion_row["all_samples_pass"])
    except Exception as exc:
        fail(report, "R2_motion_check_aborted", error=repr(exc), traceback=traceback.format_exc())
        report["checks"]["synchronous_66_sample_R2_clearance_and_overlap"] = {"pass": False, "error": repr(exc)}


def main():
    report = {
        "gate": "RampIntakeR2_saved_geometry_validation",
        "units": "mm",
        "scope": "Check only the four already-saved R2 STEP artifacts against saved R1 geometry: inventories/topology, unchanged parts and body cavity, ramp pose identities, measured lip drop, preserved stow envelope/flush, explicit mount contacts, deployed mouth void, and 66 sampled clearance pairs. No rebuild, rendering, continuous-sweep, airflow, or visual-approval claim.",
        "thresholds": {
            "saved_boolean_identity_mm3_exclusive": BOOL_IDENTITY_TOL_MM3,
            "saved_outer_lip_half_drop_deviation_mm_inclusive": DROP_TOL_MM,
            "saved_vertex_pick_residual_mm_inclusive": VERTEX_PICK_TOL_MM,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "new_pair_clearance_mm_exclusive": MIN_CLEARANCE_MM,
            "fixed_mount_body_contact_mm3_exclusive": CONTACT_EPS_MM3,
            "stowed_conservative_YZ_bbox_corner_radius_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
            "saved_solid_topology": "one valid positive-volume solid per saved leaf",
        },
        "approved_pose_values": {
            "hinge_axis_point_mm": [HINGE_X, 0.0, HINGE_Z],
            "R1_ramp_angle_deg": R1_ANGLE_DEG,
            "R2_ramp_angle_deg": R2_ANGLE_DEG,
            "R2_fraction_by_state": FRACTIONS,
        },
        "saved_artifacts": {}, "checks": {}, "failures": [],
    }
    try:
        sys.path.insert(0, str(ROOT / "src"))
        import check_ramp_intake_r1 as basecheck
        import check_tail_fin_r4 as r4check
        import check_interleaved_a5 as a5check

        full_labels = tuple((*r4check.EXPECTED_LABELS, *basecheck.NEW_LABELS))
        report["expected_inventory"] = {"full_assembly_labels": list(full_labels),
                                        "full_assembly_count": len(full_labels),
                                        "module_labels": list(NEW_LABELS),
                                        "module_count": len(NEW_LABELS)}
        r2_parts = {state: inspect_artifact(R2_PATHS[state], full_labels, report, f"R2_{state}")
                    for state in STATES}
        r2_module = inspect_artifact(R2_MODULE_PATH, NEW_LABELS, report, "R2_Module_Deployed")
        r1_parts = {state: inspect_artifact(R1_PATHS[state], full_labels, report, f"R1_{state}")
                    for state in STATES}
        r1_module = inspect_artifact(R1_MODULE_PATH, NEW_LABELS, report, "R1_Module_Deployed")
        cavity_parts = inspect_artifact(R1_BODY_CAVITY_PATH, (BODY,), report,
                                        "R1_Body_Cavity", singleton_alias=BODY)
        r4_parts = inspect_artifact(r4check.R4_PATHS["Stowed"], r4check.EXPECTED_LABELS,
                                    report, "R4_Stowed_motion_input")
        a5_parts = inspect_artifact(a5check.A5_PATHS["Stowed"], r4check.A5_LABELS,
                                    report, "A5_Stowed_motion_input")
        report["_body_cavity_parts"] = cavity_parts

        check_saved_identity(report, r1_parts, r2_parts, r1_module, r2_module, full_labels)
        check_lip_drop(report, r1_parts, r2_parts)
        check_stowed_envelope(report, r2_parts, full_labels)
        check_mount_contacts(report, r2_parts)
        check_mouth(report, r2_parts, full_labels)
        check_motion(report, r2_parts, r4_parts, a5_parts,
                     r4check, a5check, basecheck)
        report.pop("_body_cavity_parts", None)
    except Exception as exc:
        report.pop("_body_cavity_parts", None)
        fail(report, "checker_aborted_on_unexpected_exception", error=repr(exc),
             traceback=traceback.format_exc())

    report["passed"] = not report["failures"]
    motion = report["checks"].get("synchronous_66_sample_R2_clearance_and_overlap", {})
    drop = report["checks"].get("measured_saved_outer_lip_drop_is_half_R1", {})
    envelope = report["checks"].get("stowed_flush_hardware_and_125mm_envelope", {})
    report["summary"] = {
        "passed": report["passed"],
        "failure_count": len(report["failures"]),
        "saved_artifact_count": len(report["saved_artifacts"]),
        "R2_full_component_counts": {state: report["saved_artifacts"].get(f"R2_{state}", {}).get("part_count")
                                     for state in STATES},
        "R2_module_component_count": report["saved_artifacts"].get("R2_Module_Deployed", {}).get("part_count"),
        "measured_R1_lip_drop_mm": drop.get("saved_R1_measurement", {}).get("measured_mean_vertical_drop_mm"),
        "measured_R2_lip_drop_mm": drop.get("saved_R2_measurement", {}).get("measured_mean_vertical_drop_mm"),
        "half_drop_deviation_mm": drop.get("absolute_deviation_from_half_mm"),
        "minimum_sampled_clearance": motion.get("minimum_sampled_clearance"),
        "maximum_unexpected_overlap": motion.get("maximum_unexpected_overlap"),
        "motion_sample_count": motion.get("sample_count", 0),
        "stowed_radius_mm": envelope.get("maximum_conservative_radius_mm"),
        "deployed_mouth_height_mm": report["checks"].get("deployed_forward_mouth_void_clear", {}).get("unobstructed_height_mm"),
        "first_failures": report["failures"][:10],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), **report["summary"]}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
