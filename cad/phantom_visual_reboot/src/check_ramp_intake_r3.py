"""Saved-artifact validation for the 35 mm R3 ramp-intake gate.

Checks saved STEP files only. Shared import, geometry and comparison utilities
come from the prior R2 checker; this checker does not import the R3 generator.
"""

from __future__ import annotations

import itertools
import json
import math
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True

import build123d as bd


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reviews" / "ramp_intake_r3_checks.json"
STATES = ("Stowed", "Midfold", "Deployed")
FRACTIONS = {"Stowed": 0.0, "Midfold": 0.5, "Deployed": 1.0}
R1_ANGLE_DEG = 5.0
R3_ANGLE_DEG = 3.0402055284501452
TARGET_DROP_MM = 35.0
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

R3_PATHS = {state: ROOT / "STEP" / f"R_RampIntake_R3_{state}.step" for state in STATES}
R3_MODULE_PATH = ROOT / "STEP" / "R_RampIntake_R3_Module_Deployed.step"
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


def identity(report, actual, expected, check, **details):
    from check_ramp_intake_r2 import compare_geometry, measure

    return compare_geometry(measure(actual, f"actual {check}"),
                            measure(expected, f"expected {check}"),
                            report, check, **details)


def check_saved_identity(report, r1_parts, r3_parts, r1_module, r3_module,
                         cavity_parts, expected_full_labels):
    from check_ramp_intake_r2 import rotate_ramp

    nonramp_labels = tuple(label for label in expected_full_labels if label != RAMP_LABEL)
    rows_by_state = {}
    for state in STATES:
        rows = {}
        actual, reference = r3_parts.get(state, {}), r1_parts.get(state, {})
        for label in nonramp_labels:
            if label in actual and label in reference:
                rows[label] = identity(
                    report, actual[label], reference[label],
                    "R3_nonramp_part_differs_from_R1_saved_state", state=state, label=label)
        row = {"compared_count": len(rows), "expected_count": 32, "parts": rows,
               "pass": len(rows) == 32 and all(item["pass"] for item in rows.values())}
        rows_by_state[state] = row
        if len(rows) != 32:
            fail(report, "R3_nonramp_identity_coverage", state=state, expected=32,
                 actual=len(rows))
    report["checks"]["unchanged_32_nonramp_parts_match_R1"] = rows_by_state

    stowed_rows = {}
    for label in expected_full_labels:
        if label in r3_parts.get("Stowed", {}) and label in r1_parts.get("Stowed", {}):
            stowed_rows[label] = identity(
                report, r3_parts["Stowed"][label], r1_parts["Stowed"][label],
                "R3_stowed_part_differs_from_R1", state="Stowed", label=label)
    report["checks"]["all_33_stowed_parts_identical_to_R1"] = {
        "compared_count": len(stowed_rows), "expected_count": 33, "parts": stowed_rows,
        "pass": len(stowed_rows) == 33 and all(row["pass"] for row in stowed_rows.values()),
    }
    if len(stowed_rows) != 33:
        fail(report, "R3_stowed_identity_coverage", expected=33, actual=len(stowed_rows))

    pose_rows = {}
    for state in STATES:
        fraction = FRACTIONS[state]
        actual = r3_parts.get(state, {}).get(RAMP_LABEL)
        r3_stowed = r3_parts.get("Stowed", {}).get(RAMP_LABEL)
        r1_state = r1_parts.get(state, {}).get(RAMP_LABEL)
        r1_stowed = r1_parts.get("Stowed", {}).get(RAMP_LABEL)
        if any(shape is None for shape in (actual, r3_stowed, r1_state, r1_stowed)):
            fail(report, "R3_ramp_pose_identity_inputs_missing", state=state)
            pose_rows[state] = {"pass": False, "fraction": fraction}
            continue
        expected_r3_pose = rotate_ramp(r3_stowed, R3_ANGLE_DEG * fraction)
        expected_from_r1_pose = rotate_ramp(
            r1_state, (R3_ANGLE_DEG - R1_ANGLE_DEG) * fraction)
        inverse_to_r1_stowed = rotate_ramp(actual, -R3_ANGLE_DEG * fraction)
        from_stow = identity(report, actual, expected_r3_pose,
                             "R3_ramp_not_rotation_of_saved_stowed_ramp",
                             state=state, fraction=fraction,
                             rotation_deg=R3_ANGLE_DEG * fraction)
        from_r1_pose = identity(report, actual, expected_from_r1_pose,
                                "R3_ramp_not_R1_saved_pose_after_angle_correction",
                                state=state, fraction=fraction,
                                correction_deg=(R3_ANGLE_DEG - R1_ANGLE_DEG) * fraction)
        inverse_row = identity(report, inverse_to_r1_stowed, r1_stowed,
                               "R3_ramp_inverse_pose_differs_from_R1_saved_stowed_shape",
                               state=state, fraction=fraction,
                               inverse_rotation_deg=-R3_ANGLE_DEG * fraction)
        pose_rows[state] = {
            "fraction": fraction,
            "rotation_deg": R3_ANGLE_DEG * fraction,
            "from_saved_R3_stowed": from_stow,
            "from_saved_R1_pose_after_angle_correction": from_r1_pose,
            "inverse_pose_to_R1_stowed_shape": inverse_row,
            "pass": from_stow["pass"] and from_r1_pose["pass"] and inverse_row["pass"],
        }
    report["checks"]["saved_ramp_pose_and_R1_inverse_pose_identity"] = pose_rows

    module_rows = {}
    for label in NEW_LABELS:
        if label in r3_module and label in r3_parts.get("Deployed", {}):
            module_rows[label] = identity(
                report, r3_module[label], r3_parts["Deployed"][label],
                "R3_module_part_differs_from_full_deployed", state="Deployed", label=label)
        if label != RAMP_LABEL and label in r3_module and label in r1_module:
            identity(report, r3_module[label], r1_module[label],
                     "R3_module_hardware_differs_from_R1_module", state="Deployed", label=label)
    report["checks"]["deployed_module_matches_full_and_R1_hardware"] = {
        "compared_to_R3_full_count": len(module_rows), "expected_count": 4,
        "parts": module_rows,
        "pass": len(module_rows) == 4 and all(row["pass"] for row in module_rows.values()),
    }
    if len(module_rows) != 4:
        fail(report, "R3_module_identity_coverage", expected=4, actual=len(module_rows))

    cavity_rows = {}
    cavity_shape = cavity_parts.get(BODY)
    if cavity_shape is not None:
        for state in STATES:
            body_shape = r3_parts.get(state, {}).get(BODY)
            if body_shape is not None:
                cavity_rows[state] = identity(
                    report, body_shape, cavity_shape,
                    "R3_body_differs_from_saved_R1_body_cavity", state=state)
    report["checks"]["body_and_cavity_identity_unchanged"] = {
        "isolated_R1_body_cavity_path": str(ROOT / "STEP" / "R_RampIntake_R1_Body_Cavity.step"),
        "compared_full_body_states": len(cavity_rows), "expected_count": 3,
        "states": cavity_rows,
        "pass": len(cavity_rows) == 3 and all(row["pass"] for row in cavity_rows.values()),
    }
    if len(cavity_rows) != 3:
        fail(report, "R3_body_cavity_identity_coverage", expected=3, actual=len(cavity_rows))


def check_lip_drop(report, r3_parts):
    from check_ramp_intake_r2 import measure, outer_lip_drop

    try:
        measured = outer_lip_drop(
            measure(r3_parts["Stowed"][RAMP_LABEL], "R3 saved Stowed ramp"),
            measure(r3_parts["Deployed"][RAMP_LABEL], "R3 saved Deployed ramp"),
            R3_ANGLE_DEG, "R3 saved result measured from saved edge vertices")
        actual = measured["measured_mean_vertical_drop_mm"]
        deviation = abs(actual - TARGET_DROP_MM)
        row = {
            "method": ("independently pick matching lower forward-edge vertices from saved R3 STEP B-reps; "
                       "compare their actual world-Z difference to the user-specified 35 mm target; "
                       "no source formula is evaluated"),
            "target_drop_mm": TARGET_DROP_MM,
            "saved_R3_measurement": measured,
            "absolute_deviation_from_target_mm": deviation,
            "tolerance_mm_inclusive": DROP_TOL_MM,
            "pass": deviation <= DROP_TOL_MM,
        }
        report["checks"]["measured_saved_outer_lip_drop_is_35mm"] = row
        if not row["pass"]:
            fail(report, "saved_R3_outer_lip_drop_not_35mm", **row)
    except Exception as exc:
        fail(report, "saved_outer_lip_drop_measurement_error", error=repr(exc),
             traceback=traceback.format_exc())
        report["checks"]["measured_saved_outer_lip_drop_is_35mm"] = {
            "pass": False, "error": repr(exc)}


def check_stowed_envelope(report, r3_parts, expected_full_labels):
    from check_ramp_intake_r2 import measure

    try:
        parts = r3_parts["Stowed"]
        floor_min_z = float(measure(parts[RAMP_LABEL], "R3 saved stowed ramp").bounding_box().min.Z)
        hardware_min_z = {label: float(measure(parts[label], label).bounding_box().min.Z)
                          for label in NEW_LABELS[1:]}
        radii = {}
        for label in expected_full_labels:
            box = measure(parts[label], f"R3 stowed {label}").bounding_box(optimal=False)
            radii[label] = max(math.hypot(y, z)
                               for y in (float(box.min.Y), float(box.max.Y))
                               for z in (float(box.min.Z), float(box.max.Z)))
        witness = max(radii, key=radii.get)
        row = {
            "full_stowed_part_count": len(parts), "expected_part_count": 33,
            "floor_tight_min_Z_mm": floor_min_z, "belly_Z_mm": BELLY_Z,
            "stowed_floor_flush_error_mm": abs(floor_min_z - BELLY_Z),
            "stowed_floor_flush_tolerance_mm": 1.0e-6,
            "hardware_tight_min_Z_by_part_mm": hardware_min_z,
            "hardware_lowest_Z_mm": min(hardware_min_z.values()),
            "hardware_above_or_on_belly": min(hardware_min_z.values()) >= BELLY_Z,
            "conservative_YZ_AABB_corner_radius_mm_by_part": radii,
            "maximum_conservative_radius_mm": radii[witness], "radius_witness": witness,
            "radius_limit_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
            "pass": (len(parts) == 33 and abs(floor_min_z - BELLY_Z) <= 1.0e-6
                     and min(hardware_min_z.values()) >= BELLY_Z
                     and radii[witness] < STOWED_RADIUS_LIMIT_MM),
        }
        report["checks"]["stowed_flush_hardware_and_125mm_envelope"] = row
        if not row["pass"]:
            fail(report, "R3_stowed_floor_hardware_or_125mm_envelope", **row)
    except Exception as exc:
        fail(report, "R3_stowed_envelope_measurement_error", error=repr(exc),
             traceback=traceback.format_exc())


def check_mount_contacts(report, r3_parts):
    from cadgen.geometry import overlap_volume
    from check_ramp_intake_r2 import measure

    rows_by_state = {}
    for state in STATES:
        parts = r3_parts.get(state, {})
        if BODY not in parts or any(label not in parts for label in NEW_LABELS[1:3]):
            fail(report, "R3_fixed_mount_contact_inputs_missing", state=state)
            continue
        body = measure(parts[BODY], f"R3 {state} body")
        contacts = {}
        for label in NEW_LABELS[1:3]:
            amount = float(overlap_volume(measure(parts[label], f"R3 {state} {label}"), body))
            contacts[label] = {"positive_body_contact_overlap_mm3": amount,
                               "minimum_mm3_exclusive": CONTACT_EPS_MM3,
                               "pass": amount > CONTACT_EPS_MM3}
            if not contacts[label]["pass"]:
                fail(report, "R3_fixed_mount_body_contact_not_positive", state=state,
                     label=label, overlap_mm3=amount, minimum_mm3_exclusive=CONTACT_EPS_MM3)
        rows_by_state[state] = {
            "contacts": contacts, "compared_count": len(contacts), "expected_count": 2,
            "pass": len(contacts) == 2 and all(item["pass"] for item in contacts.values()),
        }
    report["checks"]["only_explicit_fixed_mount_body_contacts"] = {
        "authorized_mount_body_pairs": [sorted(pair) for pair in MOUNT_BODY_PAIRS],
        "states": rows_by_state,
        "pass": len(rows_by_state) == 3 and all(row["pass"] for row in rows_by_state.values()),
    }


def check_mouth(report, r3_parts, expected_full_labels):
    from cadgen.geometry import overlap_volume
    from check_ramp_intake_r2 import bbox_gap, measure

    try:
        floor_z = HINGE_Z - (MOUTH_X - HINGE_X) * math.tan(math.radians(R3_ANGLE_DEG))
        z0, z1 = floor_z + 0.3, BELLY_Z - 0.3
        mouth = bd.Box(0.2, 124.0, z1 - z0).translate(
            (MOUTH_X, 0.0, (z0 + z1) / 2.0)) if z1 > z0 else None
        if mouth is None:
            raise RuntimeError(f"Nonpositive mouth void height: floor={floor_z}, slab=[{z0}, {z1}]")
        deployed = r3_parts["Deployed"]
        blockers = []
        for label in expected_full_labels:
            if label not in deployed:
                continue
            shape = measure(deployed[label], f"R3 deployed mouth comparison {label}")
            if bbox_gap(mouth, shape) == 0.0:
                amount = float(overlap_volume(measure(mouth, "R3 mouth void slab"), shape))
                if amount >= OVERLAP_TOL_MM3:
                    blockers.append({"label": label, "overlap_mm3": amount})
        row = {
            "test_slab_x_mm": [MOUTH_X - 0.1, MOUTH_X + 0.1],
            "test_y_mm": [-62.0, 62.0], "floor_at_test_plane_z_mm": floor_z,
            "test_z_mm": [z0, z1], "unobstructed_width_mm": 124.0,
            "unobstructed_height_mm": z1 - z0,
            "positive_mouth_void": z1 > z0 and 124.0 > 0.0,
            "tested_final_part_count": len(deployed), "expected_final_part_count": 33,
            "blockers_ge_0_001_mm3": blockers,
            "pass": len(deployed) == 33 and z1 > z0 and not blockers,
            "interpretation": "Geometric forward mouth clearance only; no airflow-performance claim.",
        }
        report["checks"]["deployed_forward_mouth_void_positive_and_clear"] = row
        if not row["pass"]:
            fail(report, "R3_deployed_forward_mouth_obstructed_or_incomplete", **row)
    except Exception as exc:
        fail(report, "R3_mouth_measurement_error", error=repr(exc),
             traceback=traceback.format_exc())


def check_motion(report, r3_parts, r4_parts, a5_parts, r4check, a5check, basecheck):
    from check_ramp_intake_r2 import measure, pair_result, rotate_ramp

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
        body = measure(r3_parts["Stowed"][BODY], "R3 saved Stowed body")
        new_stowed = {label: measure(r3_parts["Stowed"][label], f"R3 saved Stowed {label}")
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
            posed_new[RAMP_LABEL] = rotate_ramp(new_stowed[RAMP_LABEL], R3_ANGLE_DEG * fraction)
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
                            result = pair_result(measure(new_shape, f"R3 motion {new_label}"), old_shape)
                            if cache_key:
                                cached_static_pairs[cache_key] = result
                        row = {"pair": [new_label, old_label], **result,
                               "result_reused_identical_static_geometry": bool(cache_key and sample_index > 0)}
                        pair_rows.append(row)
                    except Exception as exc:
                        errors.append({"pair": [new_label, old_label], "error": repr(exc)})
                        fail(report, "R3_motion_pair_measurement_error", sample=sample_index,
                             fraction=fraction, pair=[new_label, old_label], error=repr(exc),
                             traceback=traceback.format_exc())
                        continue
                    if sample_min["clearance_mm"] is None or row["clearance_mm"] < sample_min["clearance_mm"]:
                        sample_min = {"clearance_mm": row["clearance_mm"], "pair": row["pair"],
                                      "method": row["method"]}
                    if row["overlap_mm3"] > sample_overlap["overlap_mm3"]:
                        sample_overlap = {"overlap_mm3": row["overlap_mm3"], "pair": row["pair"]}
                    if row["clearance_mm"] < MIN_CLEARANCE_MM or row["overlap_mm3"] >= OVERLAP_TOL_MM3:
                        fail(report, "R3_intake_vs_existing_clearance_or_overlap", sample=sample_index,
                             fraction=fraction, **row, clearance_mm_exclusive=MIN_CLEARANCE_MM,
                             overlap_mm3_exclusive=OVERLAP_TOL_MM3)
            for (first_label, first_shape), (second_label, second_shape) in itertools.combinations(
                    posed_new.items(), 2):
                try:
                    result = pair_result(measure(first_shape, first_label),
                                         measure(second_shape, second_label))
                    row = {"pair": [first_label, second_label], **result,
                           "result_reused_identical_static_geometry": False}
                    pair_rows.append(row)
                except Exception as exc:
                    errors.append({"pair": [first_label, second_label], "error": repr(exc)})
                    fail(report, "R3_internal_pair_measurement_error", sample=sample_index,
                         fraction=fraction, pair=[first_label, second_label], error=repr(exc),
                         traceback=traceback.format_exc())
                    continue
                if sample_min["clearance_mm"] is None or row["clearance_mm"] < sample_min["clearance_mm"]:
                    sample_min = {"clearance_mm": row["clearance_mm"], "pair": row["pair"],
                                  "method": row["method"]}
                if row["overlap_mm3"] > sample_overlap["overlap_mm3"]:
                    sample_overlap = {"overlap_mm3": row["overlap_mm3"], "pair": row["pair"]}
                if row["clearance_mm"] < MIN_CLEARANCE_MM or row["overlap_mm3"] >= OVERLAP_TOL_MM3:
                    fail(report, "R3_internal_clearance_or_overlap", sample=sample_index,
                         fraction=fraction, **row, clearance_mm_exclusive=MIN_CLEARANCE_MM,
                         overlap_mm3_exclusive=OVERLAP_TOL_MM3)
            expected_checked = pair_count_expected - len(MOUNT_BODY_PAIRS)
            passed = (len(pair_rows) == expected_checked and exempt_count == len(MOUNT_BODY_PAIRS)
                      and not errors and all(row["clearance_mm"] > MIN_CLEARANCE_MM
                                             and row["overlap_mm3"] < OVERLAP_TOL_MM3
                                             for row in pair_rows))
            samples.append({
                "sample": sample_index, "fraction": fraction,
                "ramp_rotation_deg": R3_ANGLE_DEG * fraction,
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
                fail(report, "R3_motion_pair_coverage", sample=sample_index, fraction=fraction,
                     expected=expected_checked, actual=len(pair_rows))

        motion_row = {
            "method": ("66 saved-input synchronous pose samples: 61 uniform fractions plus five early fractions; "
                       "inherited R4/A5 reconstruction; R3 ramp rotates saved Stowed ramp by angle*f"),
            "sample_count": len(samples), "expected_sample_count": 66,
            "uniform_sample_count": 61, "early_fractions": list(basecheck.EARLY_FRACTIONS),
            "new_part_count": len(NEW_LABELS),
            "existing_part_count_per_sample": len(r4check.EXPECTED_LABELS),
            "candidate_pair_count_per_sample": pair_count_expected,
            "nonexempt_pair_count_per_sample": pair_count_expected - len(MOUNT_BODY_PAIRS),
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
        report["checks"]["synchronous_66_sample_R3_clearance_and_overlap"] = motion_row
        if not motion_row["all_samples_pass"]:
            fail(report, "R3_66_sample_motion_clearance_or_overlap_failed",
                 sample_count=len(samples), expected_sample_count=66,
                 all_samples_pass=motion_row["all_samples_pass"])
    except Exception as exc:
        fail(report, "R3_motion_check_aborted", error=repr(exc), traceback=traceback.format_exc())
        report["checks"]["synchronous_66_sample_R3_clearance_and_overlap"] = {
            "pass": False, "error": repr(exc)}


def main():
    report = {
        "gate": "RampIntakeR3_saved_geometry_validation",
        "units": "mm",
        "scope": ("Four saved R3 STEP artifacts against saved R1 geometry and R4/A5 motion inputs: "
                  "inventory/topology, 35 mm measured lip drop, unchanged parts, ramp pose/inverse-pose "
                  "identity, module identity, stowed flush/envelope, mount contacts, forward mouth void, "
                  "and 66 sampled clearance checks. No rebuild, rendering, continuous-sweep, airflow, "
                  "or visual-approval claim."),
        "thresholds": {
            "saved_boolean_identity_mm3_exclusive": BOOL_IDENTITY_TOL_MM3,
            "saved_outer_lip_target_deviation_mm_inclusive": DROP_TOL_MM,
            "saved_vertex_pick_residual_mm_inclusive": 1.0e-4,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "new_pair_clearance_mm_exclusive": MIN_CLEARANCE_MM,
            "fixed_mount_body_contact_mm3_exclusive": CONTACT_EPS_MM3,
            "stowed_conservative_YZ_bbox_corner_radius_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
            "stowed_floor_flush_tolerance_mm_inclusive": 1.0e-6,
            "saved_solid_topology": "one valid positive-volume solid per saved leaf",
        },
        "approved_pose_values": {
            "target_outer_lip_vertical_drop_mm": TARGET_DROP_MM,
            "hinge_axis_point_mm": [HINGE_X, 0.0, HINGE_Z],
            "R1_ramp_angle_deg": R1_ANGLE_DEG,
            "R3_ramp_angle_deg": R3_ANGLE_DEG,
            "R3_fraction_by_state": FRACTIONS,
        },
        "saved_artifacts": {}, "checks": {}, "failures": [],
    }
    try:
        sys.path.insert(0, str(ROOT / "src"))
        import check_ramp_intake_r1 as basecheck
        import check_ramp_intake_r2 as shared
        import check_tail_fin_r4 as r4check
        import check_interleaved_a5 as a5check

        full_labels = tuple((*r4check.EXPECTED_LABELS, *basecheck.NEW_LABELS))
        report["expected_inventory"] = {
            "full_assembly_labels": list(full_labels), "full_assembly_count": len(full_labels),
            "module_labels": list(NEW_LABELS), "module_count": len(NEW_LABELS),
        }
        r3_parts = {state: shared.inspect_artifact(
            R3_PATHS[state], full_labels, report, f"R3_{state}") for state in STATES}
        r3_module = shared.inspect_artifact(
            R3_MODULE_PATH, NEW_LABELS, report, "R3_Module_Deployed")
        r1_parts = {state: shared.inspect_artifact(
            basecheck.R1_PATHS[state], full_labels, report, f"R1_{state}") for state in STATES}
        r1_module = shared.inspect_artifact(
            basecheck.MODULE_PATHS["Deployed"], NEW_LABELS, report, "R1_Module_Deployed")
        cavity_parts = shared.inspect_artifact(
            basecheck.BODY_PATH, (BODY,), report, "R1_Body_Cavity", singleton_alias=BODY)
        r4_parts = shared.inspect_artifact(
            r4check.R4_PATHS["Stowed"], r4check.EXPECTED_LABELS, report, "R4_Stowed_motion_input")
        a5_parts = shared.inspect_artifact(
            a5check.A5_PATHS["Stowed"], r4check.A5_LABELS, report, "A5_Stowed_motion_input")

        check_saved_identity(report, r1_parts, r3_parts, r1_module, r3_module,
                             cavity_parts, full_labels)
        check_lip_drop(report, r3_parts)
        check_stowed_envelope(report, r3_parts, full_labels)
        check_mount_contacts(report, r3_parts)
        check_mouth(report, r3_parts, full_labels)
        check_motion(report, r3_parts, r4_parts, a5_parts,
                     r4check, a5check, basecheck)
    except Exception as exc:
        fail(report, "checker_aborted_on_unexpected_exception", error=repr(exc),
             traceback=traceback.format_exc())

    report["passed"] = not report["failures"]
    motion = report["checks"].get("synchronous_66_sample_R3_clearance_and_overlap", {})
    lip = report["checks"].get("measured_saved_outer_lip_drop_is_35mm", {})
    envelope = report["checks"].get("stowed_flush_hardware_and_125mm_envelope", {})
    mouth = report["checks"].get("deployed_forward_mouth_void_positive_and_clear", {})
    report["summary"] = {
        "passed": report["passed"], "failure_count": len(report["failures"]),
        "saved_artifact_count": len(report["saved_artifacts"]),
        "R3_full_component_counts": {state: report["saved_artifacts"].get(
            f"R3_{state}", {}).get("part_count") for state in STATES},
        "R3_module_component_count": report["saved_artifacts"].get(
            "R3_Module_Deployed", {}).get("part_count"),
        "measured_R3_lip_drop_mm": lip.get("saved_R3_measurement", {}).get(
            "measured_mean_vertical_drop_mm"),
        "lip_drop_deviation_from_35mm_mm": lip.get("absolute_deviation_from_target_mm"),
        "minimum_sampled_clearance": motion.get("minimum_sampled_clearance"),
        "maximum_unexpected_overlap": motion.get("maximum_unexpected_overlap"),
        "motion_sample_count": motion.get("sample_count", 0),
        "nonramp_comparison_counts_by_state": {
            state: row.get("compared_count") for state, row in report["checks"].get(
                "unchanged_32_nonramp_parts_match_R1", {}).items()},
        "stowed_radius_mm": envelope.get("maximum_conservative_radius_mm"),
        "deployed_mouth_width_mm": mouth.get("unobstructed_width_mm"),
        "deployed_mouth_height_mm": mouth.get("unobstructed_height_mm"),
        "first_failures": report["failures"][:10],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), **report["summary"]}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
