"""Saved-artifact validation for the R1 belly ramp intake gate.

The intake and body-cut expectations below are independently restated from the
approved probe dimensions. Saved STEP artifacts, not model-source outputs, are
the geometry under test. The inherited R4 checker is used only for its saved
inventory labels and the saved-A5 pose reconstruction helpers.
"""

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
REPORT_PATH = ROOT / "reviews" / "ramp_intake_r1_checks.json"
STATES = ("Stowed", "Midfold", "Deployed")
FRACTIONS_BY_STATE = {"Stowed": 0.0, "Midfold": 0.5, "Deployed": 1.0}
EARLY_FRACTIONS = (0.001, 0.002, 0.005, 0.01, 0.02)
SAMPLES = tuple(sorted(set(i / 60.0 for i in range(61)) | set(EARLY_FRACTIONS)))

BODY = "RDM9_R7_symmetric_body_20mm_wedge_R4"
NEW_LABELS = (
    "intake_r1_ramp",
    "intake_r1_fixed_mount_negative_y",
    "intake_r1_fixed_mount_positive_y",
    "intake_r1_throughpin",
)
R4_PATHS = {state: ROOT / "STEP" / f"Q_Tail_R4_Four_{state}.step" for state in STATES}
R1_PATHS = {state: ROOT / "STEP" / f"R_RampIntake_R1_{state}.step" for state in STATES}
BODY_PATH = ROOT / "STEP" / "R_RampIntake_R1_Body_Cavity.step"
MODULE_PATHS = {
    "Stowed": ROOT / "STEP" / "R_RampIntake_R1_Module_Stowed.step",
    "Deployed": ROOT / "STEP" / "R_RampIntake_R1_Module_Deployed.step",
}
A5_STOWED_PATH = ROOT / "STEP" / "O_Interleaved_A5_Stowed.step"

HINGE_X = -950.0
HINGE_Z = -83.0
RAMP_ANGLE_DEG = 5.0
FOLD_ANGLE_DEG = -135.0
BODY_BELLY_Z = -86.0
FLOOR_X = (-950.0, -290.0)
FLOOR_Y = (-64.0, 64.0)
FLOOR_Z = (-86.0, -83.0)
CHEEK_THICKNESS = 2.0
BOOL_IDENTITY_TOL_MM3 = 0.01
OVERLAP_TOL_MM3 = 0.001
CONTACT_EPS_MM3 = 1.0e-5
MIN_CLEARANCE_MM = 0.2
STOWED_RADIUS_LIMIT_MM = 125.0

MOUNT_BODY_PAIRS = {
    frozenset((NEW_LABELS[1], BODY)),
    frozenset((NEW_LABELS[2], BODY)),
}


def fail(report, check, **details):
    report["failures"].append({"check": check, **details})


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


def one_solid(shape):
    solids = list(shape.solids())
    return solids[0] if len(solids) == 1 else None


def topology(shape):
    solids = list(shape.solids())
    values = [float(solid.volume) for solid in solids]
    return {
        "valid": bool(shape.is_valid),
        "solid_count": len(solids),
        "positive_solid_volumes_mm3": values,
        "pass": bool(shape.is_valid and len(solids) == 1 and values and all(v > 0.0 for v in values)),
    }


def measure_solid(shape, description):
    """Unwrap only a temporary measurement handle; retain the saved shape itself."""
    solid = one_solid(shape)
    if solid is None:
        raise RuntimeError(f"Expected exactly one solid for {description}; got {len(list(shape.solids()))}")
    return solid


def load_parts(path):
    """Load leaf occurrences without mutating labels, styles, or saved shapes."""
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


def inventory(path, expected_labels, report, key, single_leaf_alias=None):
    try:
        if not path.is_file():
            fail(report, "required_saved_STEP_missing", artifact=key, path=str(path))
            return {}
        parts = load_parts(path)
        document_labels = sorted(parts)
        if single_leaf_alias is not None:
            if len(parts) != 1:
                raise RuntimeError(
                    f"Singleton STEP alias requires exactly one leaf; found {len(parts)} in {path}"
                )
            only_shape = next(iter(parts.values()))
            parts = {single_leaf_alias: only_shape}
        labels = sorted(parts)
        missing = sorted(set(expected_labels) - set(parts))
        extra = sorted(set(parts) - set(expected_labels))
        topologies = {label: topology(shape) for label, shape in parts.items()}
        record = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "document_labels": document_labels,
            "labels": labels,
            "part_count": len(parts),
            "expected_part_count": len(expected_labels),
            "missing_labels": missing,
            "unexpected_labels": extra,
            "topology": topologies,
        }
        report["saved_artifacts"][key] = record
        if missing or extra or len(parts) != len(expected_labels):
            fail(report, "saved_STEP_inventory", artifact=key, missing_labels=missing,
                 unexpected_labels=extra, actual_count=len(parts), expected_count=len(expected_labels))
        for label, metrics in topologies.items():
            if not metrics["pass"]:
                fail(report, "saved_component_not_single_valid_positive_solid", artifact=key,
                     label=label, topology=metrics)
        return parts
    except Exception as exc:
        fail(report, "saved_STEP_import_or_inventory_error", artifact=key, path=str(path),
             error=repr(exc), traceback=traceback.format_exc())
        return {}


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


def symdiff_volume(first, second):
    return volume(first - second) + volume(second - first)


def make_box(x0, x1, y0, y1, z0, z1):
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
    )


def cylinder_y(radius, y0, y1):
    return bd.Cylinder(radius, y1 - y0).rotate(bd.Axis.X, 90.0).translate(
        (HINGE_X, (y0 + y1) / 2.0, HINGE_Z)
    )


def union(shapes, description):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result + shape
    result = result.clean()
    if one_solid(result) is None:
        raise RuntimeError(f"Independently specified {description} did not fuse to one solid")
    return one_solid(result)


def independent_cutters():
    """R1 cutter dimensions restated from the approved probe, not the generator."""
    cavity = make_box(-953.3, -289.7, -64.3, 64.3, -100.0, -25.8)
    stub = make_box(-1030.0, -953.0, -58.0, 58.0, -77.0, -28.0)
    barrel_relief = cylinder_y(3.3, -64.3, 64.3)
    shaft_relief = cylinder_y(1.55, -71.3, 71.3)
    cap_reliefs = (
        cylinder_y(2.8, -72.3, -71.0),
        cylinder_y(2.8, 71.0, 72.3),
    )
    result = union([cavity, stub, barrel_relief, shaft_relief, *cap_reliefs], "body cutter union")
    return result, cavity, stub


def independent_cheek(y0):
    top_z = HINGE_Z + 650.0 * math.tan(math.radians(RAMP_ANGLE_DEG))
    wire = bd.Wire.make_polygon(
        [(-950.0, y0, -83.0), (-300.0, y0, -83.0), (-300.0, y0, top_z)],
        close=True,
    )
    return bd.extrude(bd.Face(wire), amount=CHEEK_THICKNESS, dir=(0.0, 1.0, 0.0))


def independent_new_parts(fraction):
    floor = make_box(*FLOOR_X, *FLOOR_Y, *FLOOR_Z)
    barrel = cylinder_y(3.0, -64.0, 64.0)
    ramp = union([floor, barrel, independent_cheek(-64.0), independent_cheek(62.0)],
                 "fused ramp before bore")
    ramp = (ramp - cylinder_y(1.5, -64.0, 64.0)).clean()
    ramp = measure_solid(ramp, "independent bored ramp")
    if fraction:
        ramp = ramp.rotate(
            bd.Axis((HINGE_X, 0.0, HINGE_Z), (0.0, 1.0, 0.0)),
            RAMP_ANGLE_DEG * fraction,
        )

    mounts = []
    for y0, y1 in ((-71.0, -65.0), (65.0, 71.0)):
        foot = make_box(-953.0, -947.0, y0, y1, -83.0, -75.0)
        mount = union([cylinder_y(3.0, y0, y1), foot], "fixed mount before bore")
        mount = (mount - cylinder_y(1.5, y0, y1)).clean()
        mounts.append(measure_solid(mount, "independent bored fixed mount"))

    pin = union([
        cylinder_y(1.25, -71.3, 71.3),
        cylinder_y(2.5, -72.0, -71.3),
        cylinder_y(2.5, 71.3, 72.0),
    ], "capped throughpin")
    return dict(zip(NEW_LABELS, (ramp, *mounts, pin)))


def radial_bbox_radius(shape):
    b = bounds(shape)
    return max(math.hypot(y, z) for y in b["y"] for z in b["z"])


def compare_geometry(actual, expected, report, check, **details):
    try:
        delta = symdiff_volume(actual, expected)
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


def body_identity(source_shape, saved_shape, cutters, report, state):
    source = measure_solid(source_shape, f"R4 {state} body")
    saved = measure_solid(saved_shape, f"R1 {state} body")
    expected = (source - cutters).clean()
    expected = measure_solid(expected, f"independently cut {state} body")
    direct_delta = symdiff_volume(saved, expected)
    saved_outside = (saved - cutters).clean()
    source_outside = (source - cutters).clean()
    outside_delta = symdiff_volume(saved_outside, source_outside)
    removed = (source - saved).clean()
    expected_removed = (source & cutters).clean()
    removed_delta = symdiff_volume(removed, expected_removed)
    added = volume(saved - source)
    passed = (direct_delta < BOOL_IDENTITY_TOL_MM3
              and outside_delta < BOOL_IDENTITY_TOL_MM3
              and removed_delta < BOOL_IDENTITY_TOL_MM3
              and added < BOOL_IDENTITY_TOL_MM3
              and topology(saved)["pass"] and topology(expected)["pass"])
    row = {
        "saved_vs_R4_minus_independent_cutters_mm3": direct_delta,
        "outside_cut_symmetric_difference_mm3": outside_delta,
        "removed_region_vs_R4_intersection_with_cutters_mm3": removed_delta,
        "added_body_material_mm3": added,
        "saved_body_topology": topology(saved),
        "independent_expected_body_topology": topology(expected),
        "pass": passed,
    }
    if not passed:
        fail(report, "body_not_exactly_R4_minus_independent_R1_cutters", state=state, **row)
    return row


def reconstruct_existing(r4check, a5check, r4_stowed, body, canonical, fraction):
    base = {label: r4_stowed[label] for label in r4check.A5_LABELS}
    posed = a5check.move_saved_stowed(
        base, fraction, canonical, a5check.CUMULATIVE_A2_DROP_MM
    )
    posed[BODY] = body
    station_axis_points = {
        station: r4check.rotate_x(bd.Vertex(0.0, 82.0, 83.0), angle).center()
        for station, angle in r4check.STATIONS
    }
    for station, _ in r4check.STATIONS:
        for suffix in r4check.TAIL_SUFFIXES:
            label = f"tail_r4_{station}_{suffix}"
            part = r4_stowed[label]
            if suffix == "fin_root" and fraction:
                point = station_axis_points[station]
                part = part.rotate(
                    bd.Axis((point.X, point.Y, point.Z), (1.0, 0.0, 0.0)),
                    r4check.FOLD_ANGLE_DEG * fraction,
                )
            posed[label] = part
    return posed


def pair_result(first, second):
    lower = bbox_gap(first, second)
    if lower > MIN_CLEARANCE_MM:
        distance = lower
        method = "disjoint_AABB_lower_bound"
        overlap = 0.0
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


def named_geometry_and_identity(r4check, a5check, report, r4_parts, r1_parts, new_expected):
    checks = report["checks"]
    old_identity = {}
    for state in STATES:
        if not r4_parts.get(state) or not r1_parts.get(state):
            continue
        rows = {}
        for label in r4check.EXPECTED_LABELS:
            if label == BODY:
                continue
            if label not in r4_parts[state] or label not in r1_parts[state]:
                continue
            rows[label] = compare_geometry(
                measure_solid(r1_parts[state][label], f"R1 {state} {label}"),
                measure_solid(r4_parts[state][label], f"R4 {state} {label}"),
                report, "nonbody_R4_component_changed", state=state, label=label,
            )
        passed = len(rows) == 28 and all(row["pass"] for row in rows.values())
        old_identity[state] = {"compared_count": len(rows), "expected_count": 28,
                               "components": rows, "pass": passed}
        if len(rows) != 28:
            fail(report, "nonbody_R4_identity_coverage", state=state,
                 expected=28, actual=len(rows))
    checks["unchanged_28_nonbody_R4_parts"] = old_identity

    new_identity = {}
    for state in STATES:
        if not r1_parts.get(state):
            continue
        rows = {}
        fraction = FRACTIONS_BY_STATE[state]
        expected = new_expected[fraction]
        for label in NEW_LABELS:
            if label not in r1_parts[state]:
                continue
            rows[label] = compare_geometry(
                measure_solid(r1_parts[state][label], f"R1 {state} {label}"),
                expected[label], report, "new_intake_part_not_independently_specified_geometry",
                state=state, label=label,
            )
        passed = len(rows) == 4 and all(row["pass"] for row in rows.values())
        new_identity[state] = {"compared_count": len(rows), "expected_count": 4,
                               "parts": rows, "pass": passed}
        if len(rows) != 4:
            fail(report, "new_intake_part_identity_coverage", state=state,
                 expected=4, actual=len(rows))
    checks["new_parts_match_independent_dimensions"] = new_identity


def check_named_pose_identity(r4check, a5check, report, r4_parts, r1_parts,
                              a5_parts, body_shape, new_expected):
    rows_by_state = {}
    try:
        r4_stowed = r4_parts["Stowed"]
        a5_stowed = a5_parts
        needed = set(a5check.PANELS) | set(a5check.SUPPORTS)
        missing = sorted(needed - set(a5_stowed))
        if missing:
            raise RuntimeError(f"Saved A5 Stowed lacks motion helper inputs: {missing}")
        canonical = {
            label: a5check.panel_canonical(
                measure_solid(a5_stowed[label], f"A5 Stowed {label}"),
                *label.split("_"), a5check.CUMULATIVE_A2_DROP_MM,
            )
            for label in a5check.PANELS
        }
        for state in ("Midfold", "Deployed"):
            if state not in r1_parts:
                continue
            fraction = FRACTIONS_BY_STATE[state]
            expected_old = reconstruct_existing(
                r4check, a5check, r4_stowed,
                measure_solid(body_shape, "R1 stowed cut body"), canonical, fraction,
            )
            expected_new = new_expected[fraction]
            expected_all = {**expected_old, **expected_new}
            actual_parts = r1_parts[state]
            rows = {}
            for label in (*r4check.EXPECTED_LABELS, *NEW_LABELS):
                if label not in actual_parts:
                    continue
                rows[label] = compare_geometry(
                    measure_solid(actual_parts[label], f"R1 {state} {label}"),
                    measure_solid(expected_all[label], f"expected rigid pose {state} {label}"),
                    report, "saved_R1_state_not_rigid_stowed_reconstruction",
                    state=state, fraction=fraction, label=label,
                )
            passed = len(rows) == 33 and all(row["pass"] for row in rows.values())
            rows_by_state[state] = {
                "fraction": fraction,
                "ramp_rotation_deg_about_Y": RAMP_ANGLE_DEG * fraction,
                "fixed_mounts_and_pin_static": True,
                "compared_count": len(rows), "expected_count": 33,
                "maximum_symmetric_difference_mm3": max(
                    (row.get("symmetric_difference_mm3", 0.0) for row in rows.values()), default=None),
                "parts": rows, "pass": passed,
            }
            if len(rows) != 33:
                fail(report, "saved_R1_pose_identity_coverage", state=state,
                     expected=33, actual=len(rows))
    except Exception as exc:
        fail(report, "saved_R1_pose_reconstruction_error", error=repr(exc),
             traceback=traceback.format_exc())
    report["checks"]["saved_midfold_and_deployed_rigid_pose_identity"] = rows_by_state
    return rows_by_state


def motion_check(r4check, a5check, report, r4_parts, a5_parts, r1_stowed,
                 new_stowed):
    body = measure_solid(r1_stowed[BODY], "R1 Stowed body for motion")
    r4_stowed = r4_parts["Stowed"]
    canonical = {
        label: a5check.panel_canonical(
            measure_solid(a5_parts[label], f"A5 Stowed {label}"),
            *label.split("_"), a5check.CUMULATIVE_A2_DROP_MM,
        )
        for label in a5check.PANELS
    }
    moving_existing = set(a5check.PANELS) | set(a5check.SUPPORTS)
    moving_existing.update(
        f"tail_r4_{station}_fin_root" for station, _ in r4check.STATIONS
    )
    expected_existing_labels = tuple(r4check.EXPECTED_LABELS)
    if set(r4_stowed) != set(expected_existing_labels):
        raise RuntimeError("R4 Stowed inventory is incomplete before motion sampling")

    samples = []
    cached_static_pairs = {}
    minimum = {"clearance_mm": None, "pair": None, "fraction": None, "method": None}
    maximum_overlap = {"overlap_mm3": 0.0, "pair": None, "fraction": None}
    pair_count_expected = 4 * 29 + 6
    for sample_index, fraction in enumerate(SAMPLES):
        existing = reconstruct_existing(r4check, a5check, r4_stowed, body, canonical, fraction)
        posed_new = dict(new_stowed)
        if fraction:
            posed_new[NEW_LABELS[0]] = posed_new[NEW_LABELS[0]].rotate(
                bd.Axis((HINGE_X, 0.0, HINGE_Z), (0.0, 1.0, 0.0)),
                RAMP_ANGLE_DEG * fraction,
            )
        pair_rows = []
        sample_minimum = {"clearance_mm": None, "pair": None, "method": None}
        worst_overlap = {"overlap_mm3": 0.0, "pair": None}
        measurement_errors = []
        exempt_count = 0
        for new_label, saved_new in posed_new.items():
            first = measure_solid(saved_new, f"posed intake {new_label}")
            for old_label in expected_existing_labels:
                old_saved = existing[old_label]
                pair_key = frozenset((new_label, old_label))
                if pair_key in MOUNT_BODY_PAIRS:
                    exempt_count += 1
                    continue
                second = measure_solid(old_saved, f"posed R4 {old_label}")
                stationary = new_label != NEW_LABELS[0] and old_label not in moving_existing
                cache_key = (new_label, old_label) if stationary else None
                try:
                    result = cached_static_pairs.get(cache_key) if cache_key else None
                    if result is None:
                        result = pair_result(first, second)
                        if cache_key:
                            cached_static_pairs[cache_key] = result
                    row = {"pair": [new_label, old_label], **result,
                           "result_reused_identical_static_geometry": bool(cache_key and sample_index > 0)}
                    pair_rows.append(row)
                    if (sample_minimum["clearance_mm"] is None
                            or row["clearance_mm"] < sample_minimum["clearance_mm"]):
                        sample_minimum = {"clearance_mm": row["clearance_mm"],
                                          "pair": row["pair"], "method": row["method"]}
                    if row["overlap_mm3"] > worst_overlap["overlap_mm3"]:
                        worst_overlap = {"overlap_mm3": row["overlap_mm3"], "pair": row["pair"]}
                    if row["overlap_mm3"] > maximum_overlap["overlap_mm3"]:
                        maximum_overlap = {"overlap_mm3": row["overlap_mm3"],
                                           "pair": row["pair"], "fraction": fraction}
                    if not row["pass"]:
                        fail(report, "intake_vs_existing_or_internal_clearance_overlap",
                             sample=sample_index, fraction=fraction, **row,
                             clearance_mm_exclusive=MIN_CLEARANCE_MM,
                             overlap_mm3_exclusive=OVERLAP_TOL_MM3)
                except Exception as exc:
                    measurement_errors.append({"pair": [new_label, old_label], "error": repr(exc)})
                    fail(report, "motion_pair_measurement_error", sample=sample_index,
                         fraction=fraction, pair=[new_label, old_label], error=repr(exc),
                         traceback=traceback.format_exc())
        for (first_label, first_shape), (second_label, second_shape) in itertools.combinations(
                posed_new.items(), 2):
            try:
                first = measure_solid(first_shape, f"posed intake {first_label}")
                second = measure_solid(second_shape, f"posed intake {second_label}")
                result = pair_result(first, second)
                row = {"pair": [first_label, second_label], **result,
                       "result_reused_identical_static_geometry": False}
                pair_rows.append(row)
                if (sample_minimum["clearance_mm"] is None
                        or row["clearance_mm"] < sample_minimum["clearance_mm"]):
                    sample_minimum = {"clearance_mm": row["clearance_mm"],
                                      "pair": row["pair"], "method": row["method"]}
                if row["overlap_mm3"] > worst_overlap["overlap_mm3"]:
                    worst_overlap = {"overlap_mm3": row["overlap_mm3"], "pair": row["pair"]}
                if row["overlap_mm3"] > maximum_overlap["overlap_mm3"]:
                    maximum_overlap = {"overlap_mm3": row["overlap_mm3"],
                                       "pair": row["pair"], "fraction": fraction}
                if not row["pass"]:
                    fail(report, "new_intake_internal_clearance_overlap", sample=sample_index,
                         fraction=fraction, **row,
                         clearance_mm_exclusive=MIN_CLEARANCE_MM,
                         overlap_mm3_exclusive=OVERLAP_TOL_MM3)
            except Exception as exc:
                measurement_errors.append({"pair": [first_label, second_label], "error": repr(exc)})
                fail(report, "internal_intake_pair_measurement_error", sample=sample_index,
                     fraction=fraction, pair=[first_label, second_label], error=repr(exc),
                     traceback=traceback.format_exc())

        if sample_minimum["clearance_mm"] is not None:
            if (minimum["clearance_mm"] is None
                    or sample_minimum["clearance_mm"] < minimum["clearance_mm"]):
                minimum = {**sample_minimum, "fraction": fraction}
        expected_nonexempt = pair_count_expected - len(MOUNT_BODY_PAIRS)
        row_pass = (len(pair_rows) == expected_nonexempt and exempt_count == len(MOUNT_BODY_PAIRS)
                    and not measurement_errors and all(row["pass"] for row in pair_rows))
        samples.append({
            "sample": sample_index,
            "fraction": fraction,
            "ramp_rotation_deg": RAMP_ANGLE_DEG * fraction,
            "R4_fin_fold_deg": FOLD_ANGLE_DEG * fraction,
            "new_part_count": len(posed_new),
            "existing_part_count": len(existing),
            "all_new_vs_existing_and_new_internal_pairs_expected": pair_count_expected,
            "nonexempt_pair_count_checked": len(pair_rows),
            "explicit_fixed_mount_body_exemptions": exempt_count,
            "minimum_clearance_mm": sample_minimum,
            "maximum_unexpected_overlap_mm3": worst_overlap,
            "measurement_error_count": len(measurement_errors),
            "pass": row_pass,
        })
        if len(pair_rows) != expected_nonexempt:
            fail(report, "motion_pair_coverage", sample=sample_index, fraction=fraction,
                 expected=expected_nonexempt, actual=len(pair_rows))

    report["checks"]["synchronous_66_sample_intake_clearance_and_overlap"] = {
        "method": ("66 synchronous pose samples: 61 uniform fractions plus five early fractions; "
                   "saved A5 helper reconstructs R4 wings/carriages/joins and saved R4 fins rotate "
                   "about their station axes; intake ramp rotates +5deg*f; mounts and pin remain static"),
        "sample_count": len(samples), "expected_sample_count": 66,
        "uniform_sample_count": 61, "early_fractions": list(EARLY_FRACTIONS),
        "new_part_count": 4, "existing_part_count_per_sample": 29,
        "candidate_pair_count_per_sample": pair_count_expected,
        "authorized_exceptions_only": [sorted(pair) for pair in sorted(MOUNT_BODY_PAIRS, key=lambda p: sorted(p))],
        "fixed_mount_body_contacts_checked_separately": True,
        "clearance_mm_exclusive": MIN_CLEARANCE_MM,
        "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
        "minimum_sampled_clearance": minimum,
        "maximum_unexpected_overlap": maximum_overlap,
        "unique_identical_static_pair_results_cached": len(cached_static_pairs),
        "all_samples_pass": len(samples) == 66 and all(row["pass"] for row in samples),
        "inherited_existing_R4_internal_motion_proof": (
            "The R4 check_tail_fin_r4.py proves old-part internal motion independently; "
            "this pass checks every new-part-to-old-part pair, including the cut body against moving parts."),
        "continuous_sweep_claim": "None; this is the specified 66-sample discrete check.",
        "samples": samples,
    }


def main():
    report = {
        "gate": "RampIntakeR1_saved_geometry_validation",
        "units": "mm",
        "scope": ("Six R1 saved STEP artifacts; independent geometry and body-cut identities; "
                  "R4 saved-state identity; named rigid poses; 66 synchronous intake/R4 motion samples; "
                  "deployed mouth slab. No source rebuild, rendering, CFD, continuous sweep, or visual approval."),
        "thresholds": {
            "saved_boolean_identity_mm3_exclusive": BOOL_IDENTITY_TOL_MM3,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "new_pair_clearance_mm_exclusive": MIN_CLEARANCE_MM,
            "fixed_mount_body_positive_contact_mm3_exclusive": CONTACT_EPS_MM3,
            "stowed_conservative_YZ_bbox_corner_radius_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
            "saved_solid_topology": "one valid positive-volume solid per saved leaf",
        },
        "independent_specification": {
            "ramp_floor_x_mm": list(FLOOR_X), "ramp_floor_y_mm": list(FLOOR_Y),
            "ramp_floor_z_mm": list(FLOOR_Z), "floor_length_mm": FLOOR_X[1] - FLOOR_X[0],
            "floor_width_mm": FLOOR_Y[1] - FLOOR_Y[0],
            "cheek_thickness_mm": CHEEK_THICKNESS,
            "hinge_axis_point_mm": [HINGE_X, 0.0, HINGE_Z],
            "ramp_deployment_deg": RAMP_ANGLE_DEG,
            "pin_shaft_radius_mm": 1.25, "ramp_and_mount_bore_radius_mm": 1.5,
            "pin_to_bore_radial_clearance_mm": 0.25,
            "cap_outer_radius_mm": 2.5,
            "cap_relief_axial_intervals_mm": [[-72.3, -71.0], [71.0, 72.3]],
            "pin_cap_axial_intervals_mm": [[-72.0, -71.3], [71.3, 72.0]],
            "cap_axial_clearance_each_end_mm": 0.3,
            "body_cutters": {
                "cavity_box_mm": {"x": [-953.3, -289.7], "y": [-64.3, 64.3], "z": [-100.0, -25.8]},
                "aft_stub_box_mm": {"x": [-1030.0, -953.0], "y": [-58.0, 58.0], "z": [-77.0, -28.0]},
                "moving_barrel_relief_radius_mm": 3.3,
                "moving_barrel_relief_y_mm": [-64.3, 64.3],
                "pin_shaft_relief_radius_mm": 1.55,
                "pin_shaft_relief_y_mm": [-71.3, 71.3],
                "pin_cap_relief_radius_mm": 2.8,
                "pin_cap_relief_y_mm": [[-72.3, -71.0], [71.0, 72.3]],
                "connection": "Cavity and aft stub overlap by 0.3 mm in X; connected cutter union required.",
                "termination": ("The stub tool ends at X=-1030 mm inside the R4 body X envelope; "
                                "the checker measures material in a terminal slab just beyond that end "
                                "and reports the remaining distance to the body's minimum-X face."),
            },
        },
        "saved_artifacts": {},
        "checks": {},
        "failures": [],
    }

    try:
        sys.path.insert(0, str(ROOT / "src"))
        import check_tail_fin_r4 as r4check
        import check_interleaved_a5 as a5check

        expected_full_labels = tuple((*r4check.EXPECTED_LABELS, *NEW_LABELS))
        r4_parts = {state: inventory(R4_PATHS[state], r4check.EXPECTED_LABELS,
                                     report, f"R4_{state}") for state in STATES}
        r1_parts = {state: inventory(R1_PATHS[state], expected_full_labels,
                                     report, f"R1_{state}") for state in STATES}
        body_parts = inventory(BODY_PATH, (BODY,), report, "R1_Body_Cavity",
                               single_leaf_alias=BODY)
        module_parts = {
            state: inventory(path, NEW_LABELS, report, f"R1_Module_{state}")
            for state, path in MODULE_PATHS.items()
        }
        a5_parts = inventory(A5_STOWED_PATH, r4check.A5_LABELS, report, "A5_Stowed_motion_input")

        cutters, cavity, stub = independent_cutters()
        report["independent_specification"]["body_cutters"].update({
            "cavity_stub_intersection_mm3": volume(cavity & stub),
            "cavity_stub_overlap_x_mm": 0.3,
            "independent_cutter_union_topology": topology(cutters),
        })
        if not topology(cutters)["pass"]:
            fail(report, "independent_body_cutter_union_not_single_valid_solid",
                 topology=topology(cutters))

        new_expected = {fraction: independent_new_parts(fraction)
                        for fraction in (0.0, 0.5, 1.0)}
        named_geometry_and_identity(r4check, a5check, report, r4_parts, r1_parts, new_expected)

        body_rows = {}
        for state in STATES:
            if state in r4_parts and BODY in r4_parts[state] and BODY in r1_parts.get(state, {}):
                body_rows[state] = body_identity(
                    r4_parts[state][BODY], r1_parts[state][BODY], cutters, report, state
                )
        report["checks"]["body_exactly_R4_minus_independent_ramp_cavity_and_reliefs"] = body_rows
        if len(body_rows) != 3:
            fail(report, "R1_body_cut_state_coverage", expected=3, actual=len(body_rows))

        isolated_identity = {}
        if BODY in body_parts and BODY in r1_parts.get("Stowed", {}):
            isolated_identity = compare_geometry(
                measure_solid(body_parts[BODY], "R1 isolated body cavity artifact"),
                measure_solid(r1_parts["Stowed"][BODY], "R1 Stowed full assembly body"),
                report, "isolated_R1_body_not_identical_to_full_Stowed_body",
                comparison="isolated body against full R1 Stowed body",
            )
        else:
            fail(report, "isolated_R1_body_identity_inputs_missing")
        report["checks"]["isolated_body_matches_full_stowed"] = isolated_identity

        module_rows = {}
        for state in ("Stowed", "Deployed"):
            if state not in module_parts or state not in r1_parts:
                continue
            rows = {}
            for label in NEW_LABELS:
                if label not in module_parts[state] or label not in r1_parts[state]:
                    continue
                rows[label] = compare_geometry(
                    measure_solid(module_parts[state][label], f"R1 Module {state} {label}"),
                    measure_solid(r1_parts[state][label], f"R1 full {state} {label}"),
                    report, "module_part_differs_from_matching_full_assembly_part",
                    state=state, label=label,
                )
            module_rows[state] = {"compared_count": len(rows), "expected_count": 4,
                                  "parts": rows,
                                  "pass": len(rows) == 4 and all(row["pass"] for row in rows.values())}
            if len(rows) != 4:
                fail(report, "module_full_part_identity_coverage", state=state,
                     expected=4, actual=len(rows))
        report["checks"]["module_parts_match_full_assembly"] = module_rows

        if cutters and r4_parts.get("Stowed") and BODY in r4_parts["Stowed"]:
            r4_body = measure_solid(r4_parts["Stowed"][BODY], "R4 Stowed source body")
            stub_terminal_slab = make_box(-1030.2, -1030.1, -58.0, 58.0, -77.0, -28.0)
            terminal_material = volume(r4_body & stub_terminal_slab)
            terminal_cut = volume(cutters & stub_terminal_slab)
            body_x_min = bounds(r4_body)["x"][0]
            stub_x_end = -1030.0
            termination = {
                "stub_terminal_x_mm": stub_x_end,
                "R4_body_minimum_X_mm": body_x_min,
                "remaining_distance_to_minimum_X_face_mm": stub_x_end - body_x_min,
                "terminal_slab_x_mm": [-1030.2, -1030.1],
                "source_body_material_in_terminal_slab_mm3": terminal_material,
                "cutter_union_in_terminal_slab_mm3": terminal_cut,
                "positive_material_after_terminal": terminal_material > 0.0 and terminal_cut < BOOL_IDENTITY_TOL_MM3,
                "pass": terminal_material > 0.0 and terminal_cut < BOOL_IDENTITY_TOL_MM3
                        and stub_x_end > body_x_min,
            }
            report["checks"]["aft_stub_blind_termination"] = termination
            if not termination["pass"]:
                fail(report, "aft_stub_blind_termination_not_measured", **termination)

        if r1_parts.get("Stowed") and all(label in r1_parts["Stowed"] for label in NEW_LABELS):
            stowed_new = {label: measure_solid(r1_parts["Stowed"][label], f"R1 Stowed {label}")
                          for label in NEW_LABELS}
            stowed_bounds = {label: bounds(shape) for label, shape in stowed_new.items()}
            tight_z_min = {
                label: float(shape.bounding_box().min.Z)
                for label, shape in stowed_new.items()
            }
            floor_z_min = tight_z_min[NEW_LABELS[0]]
            hardware_labels = NEW_LABELS[1:]
            hardware_lowest = min(tight_z_min[label] for label in hardware_labels)
            per_part_radius = {
                label: radial_bbox_radius(measure_solid(r1_parts["Stowed"][label], f"R1 Stowed {label}"))
                for label in expected_full_labels if label in r1_parts["Stowed"]
            }
            radius_witness = max(per_part_radius, key=per_part_radius.get)
            dimension_checks = {
                "floor_length_mm": FLOOR_X[1] - FLOOR_X[0],
                "floor_width_mm": FLOOR_Y[1] - FLOOR_Y[0],
                "cheek_thickness_mm": CHEEK_THICKNESS,
                "stowed_floor_outermost_Z_mm": floor_z_min,
                "stowed_floor_conservative_AABB_min_Z_mm": stowed_bounds[NEW_LABELS[0]]["z"][0],
                "stowed_floor_flush_error_mm": abs(floor_z_min - BODY_BELLY_Z),
                "stowed_hardware_lowest_Z_mm": hardware_lowest,
                "stowed_hardware_tight_min_Z_by_part_mm": {
                    label: tight_z_min[label] for label in hardware_labels
                },
                "dimension_extrema_method": "tight shape.bounding_box(); conservative AABB retained separately",
                "hardware_parts_measured": list(hardware_labels),
                "lowest_hardware_part": min(hardware_labels, key=lambda label: stowed_bounds[label]["z"][0]),
                "stowed_floor_flush_pass": abs(floor_z_min - BODY_BELLY_Z) <= 1.0e-6,
                "stowed_hardware_above_belly_pass": hardware_lowest >= BODY_BELLY_Z,
                "full_stowed_part_count": len(per_part_radius),
                "expected_full_stowed_part_count": 33,
                "conservative_YZ_bbox_corner_radius_mm_by_part": per_part_radius,
                "maximum_conservative_radius_mm": per_part_radius[radius_witness],
                "radius_witness": radius_witness,
                "radius_limit_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
                "floor_and_envelope_pass": (
                    abs(floor_z_min - BODY_BELLY_Z) <= 1.0e-6
                    and hardware_lowest >= BODY_BELLY_Z
                    and len(per_part_radius) == 33
                    and per_part_radius[radius_witness] < STOWED_RADIUS_LIMIT_MM
                ),
            }
            report["checks"]["stowed_floor_hardware_and_full_assembly_envelope"] = dimension_checks
            if not dimension_checks["floor_and_envelope_pass"]:
                fail(report, "stowed_floor_hardware_or_125mm_envelope", **dimension_checks)
        else:
            stowed_new = new_expected[0.0]
            fail(report, "stowed_floor_and_envelope_inputs_missing")

        mount_contacts = {}
        for state in STATES:
            if not r1_parts.get(state) or BODY not in r1_parts[state]:
                continue
            body_solid = measure_solid(r1_parts[state][BODY], f"R1 {state} body contact target")
            contact_rows = {}
            for label in NEW_LABELS[1:3]:
                if label not in r1_parts[state]:
                    continue
                amount = float(overlap_volume(
                    measure_solid(r1_parts[state][label], f"R1 {state} {label}"), body_solid
                ))
                contact_rows[label] = {"positive_body_contact_overlap_mm3": amount,
                                       "minimum_mm3_exclusive": CONTACT_EPS_MM3,
                                       "pass": amount > CONTACT_EPS_MM3}
                if not contact_rows[label]["pass"]:
                    fail(report, "fixed_mount_body_contact_not_positive", state=state,
                         label=label, overlap_mm3=amount, minimum_mm3_exclusive=CONTACT_EPS_MM3)
            mount_contacts[state] = {
                "compared_count": len(contact_rows), "expected_count": 2,
                "contacts": contact_rows,
                "pass": len(contact_rows) == 2 and all(row["pass"] for row in contact_rows.values()),
            }
        report["checks"]["explicit_fixed_mount_body_contacts_only"] = {
            "states": mount_contacts,
            "only_pair_exemptions": [sorted(pair) for pair in sorted(MOUNT_BODY_PAIRS, key=lambda p: sorted(p))],
            "pass": len(mount_contacts) == 3 and all(row["pass"] for row in mount_contacts.values()),
        }

        retained_old_supports = {}
        for state in STATES:
            if not r1_parts.get(state) or BODY not in r1_parts[state]:
                continue
            body_solid = measure_solid(r1_parts[state][BODY], f"R1 {state} body for old support retention")
            old_mount_rows = {}
            for station, _ in r4check.STATIONS:
                for suffix in ("fixed_knuckle_aft", "fixed_knuckle_forward"):
                    label = f"tail_r4_{station}_{suffix}"
                    if label not in r1_parts[state]:
                        continue
                    amount = float(overlap_volume(
                        measure_solid(r1_parts[state][label], f"R1 {state} {label}"), body_solid
                    ))
                    old_mount_rows[label] = {
                        "positive_body_contact_overlap_mm3": amount,
                        "minimum_mm3_exclusive": CONTACT_EPS_MM3,
                        "pass": amount > CONTACT_EPS_MM3,
                    }
                    if not old_mount_rows[label]["pass"]:
                        fail(report, "old_R4_fixed_knuckle_body_support_not_retained", state=state,
                             label=label, overlap_mm3=amount, minimum_mm3_exclusive=CONTACT_EPS_MM3)
            housing_rows = {}
            for root_label in ("starboard_fixed_root", "port_fixed_root"):
                if "supported_housing" not in r1_parts[state] or root_label not in r1_parts[state]:
                    continue
                amount = float(overlap_volume(
                    measure_solid(r1_parts[state]["supported_housing"], f"R1 {state} supported_housing"),
                    measure_solid(r1_parts[state][root_label], f"R1 {state} {root_label}"),
                ))
                housing_rows[root_label] = {
                    "positive_housing_support_overlap_mm3": amount,
                    "minimum_mm3_exclusive": CONTACT_EPS_MM3,
                    "pass": amount > CONTACT_EPS_MM3,
                }
                if not housing_rows[root_label]["pass"]:
                    fail(report, "old_R4_fixed_root_housing_support_not_retained", state=state,
                         label=root_label, overlap_mm3=amount,
                         minimum_mm3_exclusive=CONTACT_EPS_MM3)
            retained_old_supports[state] = {
                "R4_body_fixed_knuckle_contacts": {
                    "compared_count": len(old_mount_rows), "expected_count": 8,
                    "parts": old_mount_rows,
                    "pass": len(old_mount_rows) == 8 and all(row["pass"] for row in old_mount_rows.values()),
                },
                "two_A5_fixed_root_housing_supports": {
                    "compared_count": len(housing_rows), "expected_count": 2,
                    "parts": housing_rows,
                    "pass": len(housing_rows) == 2 and all(row["pass"] for row in housing_rows.values()),
                },
            }
        report["checks"]["old_R4_fixed_supports_retained_after_body_cut"] = retained_old_supports

        named_poses = {}
        if (r4_parts.get("Stowed") and a5_parts and r1_parts.get("Stowed")
                and BODY in r1_parts["Stowed"]):
            named_poses = check_named_pose_identity(
                r4check, a5check, report, r4_parts, r1_parts, a5_parts,
                r1_parts["Stowed"][BODY], new_expected,
            )
            motion_check(r4check, a5check, report, r4_parts, a5_parts,
                         r1_parts["Stowed"], stowed_new)
        else:
            fail(report, "motion_check_saved_inputs_missing")

        if r1_parts.get("Deployed"):
            mouth_x = -305.0
            floor_z = HINGE_Z - math.tan(math.radians(RAMP_ANGLE_DEG)) * (mouth_x - HINGE_X)
            z0, z1 = floor_z + 0.3, BODY_BELLY_Z - 0.3
            mouth = measure_solid(
                make_box(mouth_x - 0.1, mouth_x + 0.1, -62.0, 62.0, z0, z1),
                "deployed mouth test slab",
            )
            blockers = []
            deployed_shapes = {
                label: measure_solid(r1_parts["Deployed"][label], f"saved R1 Deployed {label}")
                for label in expected_full_labels if label in r1_parts["Deployed"]
            }
            for label, shape in deployed_shapes.items():
                solid = measure_solid(shape, f"deployed mouth comparison {label}")
                if bbox_gap(mouth, solid) == 0.0:
                    amount = float(overlap_volume(mouth, solid))
                    if amount >= OVERLAP_TOL_MM3:
                        blockers.append({"label": label, "overlap_mm3": amount})
            mouth_row = {
                "test_slab_x_mm": [mouth_x - 0.1, mouth_x + 0.1],
                "test_y_mm": [-62.0, 62.0],
                "floor_at_test_plane_z_mm": floor_z,
                "test_z_mm": [z0, z1],
                "unobstructed_width_mm": 124.0,
                "unobstructed_height_mm": z1 - z0,
                "tested_final_part_count": len(deployed_shapes),
                "blockers_ge_0_001_mm3": blockers,
                "pass": z1 > z0 and len(deployed_shapes) == 33 and not blockers,
                "interpretation": "Geometric deployed mouth clearance only; no CFD or airflow-performance claim.",
            }
            report["checks"]["deployed_forward_mouth_slab_unobstructed"] = mouth_row
            if not mouth_row["pass"]:
                fail(report, "deployed_forward_mouth_obstructed_or_incomplete", **mouth_row)
        else:
            fail(report, "deployed_mouth_check_saved_inputs_missing")

    except Exception as exc:
        fail(report, "checker_aborted_on_unexpected_exception", error=repr(exc),
             traceback=traceback.format_exc())

    report["passed"] = not report["failures"]
    report["summary"] = {
        "passed": report["passed"],
        "failure_count": len(report["failures"]),
        "saved_artifact_count": len(report["saved_artifacts"]),
        "full_state_component_counts": {
            state: report["saved_artifacts"].get(f"R1_{state}", {}).get("part_count")
            for state in STATES
        },
        "body_cut_state_count": len(report["checks"].get(
            "body_exactly_R4_minus_independent_ramp_cavity_and_reliefs", {})),
        "old_R4_nonbody_comparisons": sum(
            row.get("compared_count", 0) for row in report["checks"].get(
                "unchanged_28_nonbody_R4_parts", {}).values()),
        "motion_sample_count": len(report["checks"].get(
            "synchronous_66_sample_intake_clearance_and_overlap", {}).get("samples", [])),
        "motion_minimum_clearance": report["checks"].get(
            "synchronous_66_sample_intake_clearance_and_overlap", {}).get("minimum_sampled_clearance"),
        "motion_maximum_overlap": report["checks"].get(
            "synchronous_66_sample_intake_clearance_and_overlap", {}).get("maximum_unexpected_overlap"),
        "stowed_radius_mm": report["checks"].get(
            "stowed_floor_hardware_and_full_assembly_envelope", {}).get("maximum_conservative_radius_mm"),
        "deployed_mouth_height_mm": report["checks"].get(
            "deployed_forward_mouth_slab_unobstructed", {}).get("unobstructed_height_mm"),
        "deployed_mouth_width_mm": report["checks"].get(
            "deployed_forward_mouth_slab_unobstructed", {}).get("unobstructed_width_mm"),
        "first_failures": report["failures"][:10],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), **report["summary"]}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
