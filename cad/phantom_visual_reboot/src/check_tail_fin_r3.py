"""Saved-STEP validation for the Tail R3 recessed-fin gate.

This checker reads saved STEP artifacts only.  It does not rebuild or modify
the model, and its body cutters and Tall fin geometry are restated here rather
than imported from the R3 generator.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import traceback
from pathlib import Path

import build123d as bd
from cadgen.geometry import closest_points, overlap_volume


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reviews" / "tail_fin_r3_checks.json"
STATES = ("Stowed", "Midfold", "Deployed")
STATE_FRACTIONS = {"Stowed": 0.0, "Midfold": 0.5, "Deployed": 1.0}
EARLY_FRACTIONS = (0.001, 0.002, 0.005, 0.01, 0.02)
FOLD_SAMPLES = tuple(sorted(set(i / 60.0 for i in range(61)) | set(EARLY_FRACTIONS)))
BODY = "RDM9_R7_symmetric_body_20mm_wedge_R4"
FIN = "tail_r1_fin_root"
SUPPORTS = ("tail_r1_fixed_knuckle_aft", "tail_r1_fixed_knuckle_forward")
PIN = "tail_r1_throughpin"
TAIL_LABELS = (FIN, *SUPPORTS, PIN)
A5_LABELS = (
    BODY, "port_carriage", "port_fixed_root", "port_front", "port_join", "port_rear",
    "starboard_carriage", "starboard_fixed_root", "starboard_front", "starboard_join",
    "starboard_rear", "supported_housing", "top_cover",
)
R3_LABELS = (*A5_LABELS, *TAIL_LABELS)
R3_PATHS = {s: ROOT / "STEP" / f"Q_Tail_R3_Recessed_{s}.step" for s in STATES}
A5_PATHS = {s: ROOT / "STEP" / f"O_Interleaved_A5_{s}.step" for s in STATES}
R2_STOWED_PATH = ROOT / "STEP" / "Q_Tail_R2_Clipped_Stowed.step"
BODY_POCKET_PATH = ROOT / "STEP" / "Q_Tail_R3_Recessed_Body_Pocket.step"

SHIFT_X = -80.0
HARDWARE_DROP_Z = -5.5
HINGE_Y = 82.0
R3_HINGE_Z = 83.0
R2_HINGE_Z = 88.5
FOLD_ANGLE_DEG = -135.0
PANEL_Z = (83.0, 86.0)
R2_PANEL_Z = (87.0, 90.0)
ROOT_X = (-1325.0, -1085.0)
POCKET_OFFSET = 0.3
BODY_POCKET_FLOOR_Z = 82.7
BODY_HINGE_RELIEF_FLOOR_Z = 79.7
OVERLAP_TOL_MM3 = 0.001
BODY_DIFF_TOL_MM3 = 0.01
STATE_DIFF_TOL_MM3 = 0.01
CLEARANCE_MM = 0.2
CONTACT_EPS_MM3 = 1.0e-5
BOUND_TOL_MM = 1.0e-6
ENVELOPE_LIMIT_MM = 125.0
RADIAL_BORE_MM = 1.5
IDENTITY_AXIS = bd.Axis((0.0, HINGE_Y, R3_HINGE_Z), (1.0, 0.0, 0.0))


def add_failure(report, check, **details):
    report["failures"].append({"check": check, **details})


def bounds(shape):
    box = shape.bounding_box(optimal=False)
    return {
        "x": [float(box.min.X), float(box.max.X)],
        "y": [float(box.min.Y), float(box.max.Y)],
        "z": [float(box.min.Z), float(box.max.Z)],
    }


def bbox_gap(first, second):
    a, b = bounds(first), bounds(second)
    gaps = [max(0.0, a[axis][0] - b[axis][1], b[axis][0] - a[axis][1]) for axis in ("x", "y", "z")]
    return math.sqrt(sum(gap * gap for gap in gaps))


def symdiff_volume(first, second):
    return float((first - second).volume) + float((second - first).volume)


def topology(shape):
    solids = list(shape.solids())
    volumes = [float(solid.volume) for solid in solids]
    return {
        "valid": bool(shape.is_valid),
        "solid_count": len(solids),
        "positive_volumes_mm3": volumes,
        "pass": bool(shape.is_valid and len(solids) == 1 and volumes and all(v > 0.0 for v in volumes)),
    }


def flatten_step(path):
    root = bd.import_step(str(path))
    leaves = []

    def visit(node):
        children = list(getattr(node, "children", ()) or ())
        if children:
            for child in children:
                visit(child)
        else:
            leaves.append(node)

    visit(root)
    parts = {}
    duplicates = []
    for part in leaves:
        label = str(part.label)
        if label in parts:
            duplicates.append(label)
        solids = list(part.solids())
        if len(solids) == 1:
            solids[0].label = label
            parts[label] = solids[0]
        else:
            parts[label] = part
    if duplicates:
        raise RuntimeError(f"Duplicate STEP labels in {path}: {duplicates}")
    return parts


def read_inventory(path, expected, report, key):
    if not path.is_file():
        add_failure(report, "required_saved_STEP_missing", artifact=key, path=str(path))
        return {}
    try:
        parts = flatten_step(path)
        saved_labels = sorted(parts)
        # cadgen names a singleton STEP document by its output stem. Accept
        # only this known standalone alias; retain strict component inventories
        # in assemblies and the exact isolated-body Boolean checks below.
        if key == 'R3_Body_Pocket' and set(parts) == {'Q_Tail_R3_Recessed_Body_Pocket'}:
            parts = {BODY: parts['Q_Tail_R3_Recessed_Body_Pocket']}
        missing = sorted(set(expected) - set(parts))
        extra = sorted(set(parts) - set(expected))
        topologies = {name: topology(shape) for name, shape in parts.items()}
        report["saved_artifacts"][key] = {
            "path": str(path), "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "part_count": len(parts), "expected_part_count": len(expected),
            "labels": sorted(parts), "missing_labels": missing,
            "saved_document_labels": saved_labels,
            "unexpected_labels": extra, "topology": topologies,
        }
        if missing or extra or len(parts) != len(expected):
            add_failure(report, "saved_STEP_inventory", artifact=key,
                        missing_labels=missing, unexpected_labels=extra,
                        actual_count=len(parts), expected_count=len(expected))
        for label, metrics in topologies.items():
            if not metrics["pass"]:
                add_failure(report, "saved_component_not_single_valid_positive_solid",
                            artifact=key, label=label, metrics=metrics)
        return parts
    except Exception as exc:
        add_failure(report, "saved_STEP_import", artifact=key, path=str(path),
                    error=repr(exc), traceback=traceback.format_exc())
        return {}


def cylinder_x(radius, x0, x1, y, z):
    return bd.Cylinder(radius, x1 - x0,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER)) \
        .rotate(bd.Axis.Y, 90.0).translate(((x0 + x1) / 2.0, y, z))


def pocket_cutters():
    # Tall planform translated aft 80 mm: XY vertices are independently fixed.
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
        cylinder_x(3.3, -1325.3, -1084.7, HINGE_Y, R3_HINGE_Z),
        cylinder_x(1.55, -1335.6, -1074.4, HINGE_Y, R3_HINGE_Z),
        cylinder_x(2.8, -1336.3, -1335.0, HINGE_Y, R3_HINGE_Z),
        cylinder_x(2.8, -1075.0, -1073.7, HINGE_Y, R3_HINGE_Z),
    ]


def cutter_union():
    cutters = pocket_cutters()
    result = cutters[0]
    for cutter in cutters[1:]:
        result = result + cutter
    return result.clean()


def expected_fin(z_panel, z_hinge):
    panel = bd.extrude(
        bd.Face(bd.Wire.make_polygon(
            [(-1325.0, 82.0, z_panel), (-1085.0, 82.0, z_panel),
             (-1180.0, -28.0, z_panel), (-1280.0, -28.0, z_panel)],
            close=True)),
        amount=3.0, dir=(0, 0, 1),
    )
    barrel = cylinder_x(3.0, *ROOT_X, HINGE_Y, z_hinge)
    bore = cylinder_x(RADIAL_BORE_MM, ROOT_X[0] - 0.1, ROOT_X[1] + 0.1,
                      HINGE_Y, z_hinge)
    return ((panel + barrel).clean() - bore).clean()


def exact_minimum(pairs):
    """Exact closest distance with rigorous disjoint-AABB lower-bound pruning."""
    candidates = sorted((bbox_gap(first, second), name, first, second)
                        for name, first, second in pairs)
    best = math.inf
    witness = None
    exact_count = 0
    overlaps = []
    for lower, name, first, second in candidates:
        if lower > best:
            continue
        overlap = float(overlap_volume(first, second))
        distance = float(closest_points(first, second).distance)
        exact_count += 1
        if overlap >= OVERLAP_TOL_MM3:
            overlaps.append({"pair": name, "overlap_mm3": overlap})
        if distance < best:
            best, witness = distance, name
    return {
        "minimum_clearance_mm": None if math.isinf(best) else best,
        "witness_pair": witness,
        "exact_pairs_tested": exact_count,
        "AABB_pairs_pruned": len(candidates) - exact_count,
        "unexpected_overlaps_ge_0_001_mm3": overlaps,
    }


def radial_bound(shape):
    b = bounds(shape)
    return math.hypot(max(abs(v) for v in b["y"]), max(abs(v) for v in b["z"]))


def bbox_corner_radial_bound(shape):
    b = bounds(shape)
    return max(math.hypot(y, z) for y in b["y"] for z in b["z"])


def pass_clearance(result):
    return (result["minimum_clearance_mm"] is not None
            and result["minimum_clearance_mm"] > CLEARANCE_MM
            and not result["unexpected_overlaps_ge_0_001_mm3"])


def main():
    report = {
        "gate": "TailR3_saved_geometry_validation",
        "units": "mm",
        "scope": "Saved R3/A5/R2 STEP checks only; no model rebuild, rendering, or visual approval.",
        "thresholds": {
            "saved_body_symmetric_difference_mm3_exclusive": BODY_DIFF_TOL_MM3,
            "saved_pose_symmetric_difference_mm3_exclusive": STATE_DIFF_TOL_MM3,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "motion_clearance_mm_exclusive": CLEARANCE_MM,
            "positive_foot_and_knuckle_body_contact_mm3_exclusive": CONTACT_EPS_MM3,
            "outer_body_X_endpoint_tolerance_mm": BOUND_TOL_MM,
            "assembly_conservative_YZ_envelope_mm_exclusive": ENVELOPE_LIMIT_MM,
            "fold_samples": list(FOLD_SAMPLES),
            "fold_axis_point_and_direction": [[0.0, HINGE_Y, R3_HINGE_Z], [1.0, 0.0, 0.0]],
            "fold_angle_deg": FOLD_ANGLE_DEG,
        },
        "saved_artifacts": {}, "checks": {}, "failures": [],
    }

    r3, a5 = {}, {}
    for state in STATES:
        r3[state] = read_inventory(R3_PATHS[state], R3_LABELS, report, f"R3_{state}")
        a5[state] = read_inventory(A5_PATHS[state], A5_LABELS, report, f"A5_{state}")
    r2 = read_inventory(R2_STOWED_PATH, R3_LABELS, report, "R2_Stowed_reference")
    body_pocket_parts = read_inventory(BODY_POCKET_PATH, (BODY,), report, "R3_Body_Pocket")

    # Exact identity for untouched A5 leaves, and independently reconstructed
    # prescribed boolean subtraction for the body in every saved state.
    cutter = cutter_union()
    base_identity = {}
    body_metrics = {}
    for state in STATES:
        out, base = r3[state], a5[state]
        row = {}
        for label in A5_LABELS:
            if label == BODY or label not in out or label not in base:
                continue
            try:
                delta = symdiff_volume(out[label], base[label])
                row[label] = delta
                if delta >= BODY_DIFF_TOL_MM3:
                    add_failure(report, "nonbody_A5_component_changed", state=state,
                                label=label, symmetric_difference_mm3=delta)
            except Exception as exc:
                add_failure(report, "nonbody_A5_boolean_comparison", state=state,
                            label=label, error=repr(exc))
        base_identity[state] = {
            "compared_count": len(row), "expected_count": len(A5_LABELS) - 1,
            "symmetric_difference_mm3_by_label": row,
            "pass": len(row) == len(A5_LABELS) - 1 and all(v < BODY_DIFF_TOL_MM3 for v in row.values()),
        }
        if len(row) != len(A5_LABELS) - 1:
            add_failure(report, "nonbody_A5_identity_coverage", state=state,
                        expected=len(A5_LABELS) - 1, actual=len(row))

        if BODY in out and BODY in base:
            try:
                expected_body = (base[BODY] - cutter).clean()
                delta = symdiff_volume(out[BODY], expected_body)
                removed = (base[BODY] - out[BODY]).clean()
                expected_removed = (base[BODY] & cutter).clean()
                removed_delta = symdiff_volume(removed, expected_removed)
                metrics = {
                    "expected_body_symdiff_mm3": delta,
                    "removed_region_symdiff_mm3": removed_delta,
                    "expected_body_topology": topology(expected_body),
                    "saved_body_topology": topology(out[BODY]),
                    "source_body_bounds_mm": bounds(base[BODY]),
                    "saved_body_bounds_mm": bounds(out[BODY]),
                    "pass": (delta < BODY_DIFF_TOL_MM3 and removed_delta < BODY_DIFF_TOL_MM3
                             and topology(expected_body)["pass"] and topology(out[BODY])["pass"]),
                }
                body_metrics[state] = metrics
                if not metrics["pass"]:
                    add_failure(report, "body_not_exactly_prescribed_pocket_and_reliefs",
                                state=state, **metrics)
            except Exception as exc:
                add_failure(report, "body_cutter_boolean_comparison", state=state,
                            error=repr(exc), traceback=traceback.format_exc())
    report["checks"]["unchanged_nonbody_A5_components"] = base_identity
    report["checks"]["body_declared_cut_only"] = body_metrics

    # The isolated body-pockets STEP must be the same solid as the stowed
    # assembly's recessed body, and independently equal A5 stowed minus tools.
    pocket_identity = {}
    if BODY in body_pocket_parts and BODY in a5["Stowed"] and BODY in r3["Stowed"]:
        try:
            expected = (a5["Stowed"][BODY] - cutter).clean()
            from_expected = symdiff_volume(body_pocket_parts[BODY], expected)
            from_assembly = symdiff_volume(body_pocket_parts[BODY], r3["Stowed"][BODY])
            pocket_identity = {
                "body_pocket_vs_A5_stowed_minus_cutters_mm3": from_expected,
                "body_pocket_vs_R3_stowed_body_mm3": from_assembly,
                "pass": from_expected < BODY_DIFF_TOL_MM3 and from_assembly < BODY_DIFF_TOL_MM3,
            }
            if not pocket_identity["pass"]:
                add_failure(report, "isolated_body_pocket_identity", **pocket_identity)
        except Exception as exc:
            add_failure(report, "isolated_body_pocket_boolean_comparison", error=repr(exc))
    else:
        add_failure(report, "isolated_body_pocket_comparison_inputs_missing")
    report["checks"]["isolated_body_pocket_identity"] = pocket_identity

    # Validate the stowed fin against an independent Tall panel/barrel/bore
    # construction; also validate the R2 Tall geometry and its translated fixed
    # hardware references.  R3 intentionally changes barrel-to-panel Z relation.
    fin_geometry = {}
    if FIN in r3["Stowed"]:
        try:
            expected_r3_fin = expected_fin(PANEL_Z[0], R3_HINGE_Z)
            r3_delta = symdiff_volume(r3["Stowed"][FIN], expected_r3_fin)
            r2_delta = None
            if FIN in r2:
                expected_r2_fin = expected_fin(R2_PANEL_Z[0], R2_HINGE_Z)
                r2_delta = symdiff_volume(r2[FIN], expected_r2_fin)
            panel_area = float(bd.Face(bd.Wire.make_polygon(
                [(-1325.0, 82.0, 0), (-1085.0, 82.0, 0),
                 (-1180.0, -28.0, 0), (-1280.0, -28.0, 0)], close=True)).area)
            b = bounds(r3["Stowed"][FIN])
            fin_geometry = {
                "independent_R3_fin_symmetric_difference_mm3": r3_delta,
                "independent_saved_R2_fin_symmetric_difference_mm3": r2_delta,
                "panel_planform_xy_mm": [[-1325.0, 82.0], [-1085.0, 82.0],
                                          [-1180.0, -28.0], [-1280.0, -28.0]],
                "panel_planform_area_mm2": panel_area,
                "panel_thickness_mm": PANEL_Z[1] - PANEL_Z[0],
                "R2_panel_thickness_mm": R2_PANEL_Z[1] - R2_PANEL_Z[0],
                "saved_fin_bounds_mm": b,
                "panel_outer_face_z_expected_mm": 86.0,
                "R2_panel_z_mm": list(R2_PANEL_Z),
                "R2_hinge_axis_z_mm": R2_HINGE_Z,
                "R3_panel_z_mm": list(PANEL_Z),
                "R3_hinge_axis_z_mm": R3_HINGE_Z,
                "pin_bore_radius_mm": RADIAL_BORE_MM,
                "root_relation_intentionally_changed": (R2_HINGE_Z - R2_PANEL_Z[0]
                                                        != R3_HINGE_Z - PANEL_Z[0]),
                "pass": (r3_delta < BODY_DIFF_TOL_MM3
                         and (r2_delta is None or r2_delta < BODY_DIFF_TOL_MM3)
                         and PANEL_Z[1] - PANEL_Z[0] == R2_PANEL_Z[1] - R2_PANEL_Z[0]
                         and abs(b["z"][1] - 86.0) <= BOUND_TOL_MM
                         and abs(b["x"][0] - ROOT_X[0]) <= BOUND_TOL_MM
                         and abs(b["x"][1] - ROOT_X[1]) <= BOUND_TOL_MM),
            }
            if not fin_geometry["pass"]:
                add_failure(report, "independent_R3_fin_geometry", **fin_geometry)
        except Exception as exc:
            add_failure(report, "independent_R3_fin_geometry_measurement", error=repr(exc),
                        traceback=traceback.format_exc())

    hardware_identity = {}
    if all(label in r2 for label in (*SUPPORTS, PIN)):
        for state in STATES:
            row = {}
            for label in (*SUPPORTS, PIN):
                if label not in r3[state]:
                    continue
                expected = r2[label].translate((0.0, 0.0, HARDWARE_DROP_Z))
                delta = symdiff_volume(r3[state][label], expected)
                row[label] = delta
                if delta >= BODY_DIFF_TOL_MM3:
                    add_failure(report, "fixed_hardware_not_saved_R2_counterpart_lowered_5_5_mm",
                                state=state, label=label, symmetric_difference_mm3=delta)
            hardware_identity[state] = {
                "compared_count": len(row), "expected_count": 3,
                "symmetric_difference_mm3_by_label": row,
                "pass": len(row) == 3 and all(v < BODY_DIFF_TOL_MM3 for v in row.values()),
            }
            if len(row) != 3:
                add_failure(report, "fixed_hardware_reference_coverage", state=state,
                            expected=3, actual=len(row))

    pose_identity = {}
    if FIN in r3["Stowed"]:
        for state in STATES:
            if FIN not in r3[state]:
                continue
            fraction = STATE_FRACTIONS[state]
            expected = r3["Stowed"][FIN].rotate(IDENTITY_AXIS, FOLD_ANGLE_DEG * fraction)
            delta = symdiff_volume(r3[state][FIN], expected)
            pose_identity[state] = {"fraction": fraction, "angle_deg": FOLD_ANGLE_DEG * fraction,
                                    "fin_symmetric_difference_mm3": delta,
                                    "pass": delta < STATE_DIFF_TOL_MM3}
            if delta >= STATE_DIFF_TOL_MM3:
                add_failure(report, "saved_R3_fin_not_rigid_fold_of_saved_stowed_fin",
                            state=state, symmetric_difference_mm3=delta)
    if len(pose_identity) != len(STATES):
        add_failure(report, "saved_R3_fin_pose_coverage", expected=len(STATES), actual=len(pose_identity))
    report["checks"]["independent_fin_geometry"] = fin_geometry
    report["checks"]["saved_R2_hardware_identity_after_Z_drop"] = hardware_identity
    report["checks"]["saved_fin_pose_identity"] = pose_identity

    # Cutter datum, imported outer-X tolerance, and conservative whole assembly
    # envelope are measured from the saved geometry rather than probe claims.
    cutter_bounds = [bounds(tool) for tool in pocket_cutters()]
    cutter_checks = {
        "broad_pocket_floor_z_mm": cutter_bounds[0]["z"][0],
        "hinge_relief_floor_z_mm": bounds(pocket_cutters()[1])["z"][0],
        "broad_pocket_floor_pass": abs(cutter_bounds[0]["z"][0] - BODY_POCKET_FLOOR_Z) <= BOUND_TOL_MM,
        "hinge_relief_floor_pass": abs(bounds(pocket_cutters()[1])["z"][0] - BODY_HINGE_RELIEF_FLOOR_Z) <= BOUND_TOL_MM,
        "outer_X_endpoint_tolerance_mm": BOUND_TOL_MM,
        "states": {},
    }
    for state in STATES:
        parts = r3[state]
        if not all(label in parts for label in R3_LABELS):
            continue
        body_bounds = bounds(parts[BODY])
        outer_x_pass = (abs(body_bounds["x"][0] + 1400.0) <= BOUND_TOL_MM
                        and abs(body_bounds["x"][1] - 1400.0) <= BOUND_TOL_MM)
        per_component_envelopes = {
            label: bbox_corner_radial_bound(parts[label]) for label in R3_LABELS
        }
        envelope_witness = max(per_component_envelopes, key=per_component_envelopes.get)
        assembly_radial = per_component_envelopes[envelope_witness]
        tail_radii = {label: radial_bound(parts[label]) for label in TAIL_LABELS}
        envelope_applies = state == "Stowed"
        envelope_pass = assembly_radial < ENVELOPE_LIMIT_MM if envelope_applies else None
        state_pass = outer_x_pass and (not envelope_applies or envelope_pass)
        cutter_checks["states"][state] = {
            "body_X_bounds_mm": body_bounds["x"],
            "body_outer_X_expected_mm": [-1400.0, 1400.0],
            "body_outer_X_pass": outer_x_pass,
            "whole_assembly_conservative_YZ_envelope_mm": assembly_radial,
            "whole_assembly_envelope_witness_component": envelope_witness,
            "per_component_conservative_YZ_box_envelopes_mm": per_component_envelopes,
            "tail_components_conservative_YZ_radii_mm": tail_radii,
            "tail_only_max_conservative_YZ_radius_mm": max(tail_radii.values()),
            "125_mm_envelope_gate_applies": envelope_applies,
            "whole_assembly_envelope_under_125_mm": envelope_pass,
            "pass": state_pass,
        }
        if not outer_x_pass:
            add_failure(report, "saved_body_outer_X_not_within_1e_6_mm",
                        state=state, measured_mm=body_bounds["x"], expected_mm=[-1400.0, 1400.0],
                        tolerance_mm=BOUND_TOL_MM)
        if envelope_applies and not envelope_pass:
            add_failure(report, "whole_assembly_envelope_not_below_125_mm",
                        state=state, measured_mm=assembly_radial, limit_mm=ENVELOPE_LIMIT_MM)
    if not cutter_checks["broad_pocket_floor_pass"] or not cutter_checks["hinge_relief_floor_pass"]:
        add_failure(report, "independent_cutter_floor_datums", metrics=cutter_checks)
    report["checks"]["pocket_datums_and_envelopes"] = cutter_checks

    # Saved state collision coverage includes every tail-to-A5 pair and every
    # tail-mutual pair, matching the prior tail-gate coverage (A5-A5 is out of scope).
    # Only the two fixed support/body pairs are authorized, and they are split
    # and positively measured in the separate contact check below.
    interactions = {}
    contacts = {}
    hardware_clearance = {}
    for state in STATES:
        parts = r3[state]
        if not all(label in parts for label in R3_LABELS):
            continue
        unexpected = []
        exact_pairs = 0
        authorized_pair_names = []
        interaction_pairs = [(tail_label, base_label)
                             for tail_label in TAIL_LABELS for base_label in A5_LABELS]
        interaction_pairs.extend(
            (TAIL_LABELS[i], TAIL_LABELS[j])
            for i in range(len(TAIL_LABELS)) for j in range(i + 1, len(TAIL_LABELS))
        )
        for first_label, second_label in interaction_pairs:
            allowed = ((first_label in SUPPORTS and second_label == BODY)
                       or (first_label == BODY and second_label in SUPPORTS))
            if allowed:
                authorized_pair_names.append([first_label, second_label])
                continue
            first, second = parts[first_label], parts[second_label]
            if bbox_gap(first, second) > 0.0:
                continue
            exact_pairs += 1
            amount = float(overlap_volume(first, second))
            if amount >= OVERLAP_TOL_MM3:
                unexpected.append({"pair": [first_label, second_label], "overlap_mm3": amount})
        interactions[state] = {
            "tail_A5_and_tail_mutual_pair_coverage": len(interaction_pairs),
            "scope": "all 4 tail components vs all 13 A5 components plus all 6 tail-mutual pairs; no A5-A5 pairs",
            "authorized_support_body_pairs": authorized_pair_names,
            "AABB_intersecting_nonexception_pairs_exactly_tested": exact_pairs,
            "unexpected_overlaps_ge_0_001_mm3": unexpected,
            "pass": not unexpected,
        }
        if unexpected:
            add_failure(report, "saved_state_unexpected_component_overlap", state=state, overlaps=unexpected)

        body = parts[BODY]
        contact_state = {}
        for label, (x0, x1) in zip(SUPPORTS, ((-1335.0, -1326.0), (-1084.0, -1075.0))):
            foot_box = bd.Solid.make_box(x1 - x0, 5.5, 8.5,
                                         plane=bd.Plane(origin=(x0, 79.0, 74.5)))
            support = parts[label]
            foot = (support & foot_box).clean()
            knuckle = (support - foot_box).clean()
            foot_overlap = float(overlap_volume(foot, body))
            knuckle_overlap = float(overlap_volume(knuckle, body))
            total_overlap = float(overlap_volume(support, body))
            partition_delta = abs(total_overlap - (foot_overlap + knuckle_overlap))
            row = {
                "foot_body_overlap_mm3": foot_overlap,
                "knuckle_body_overlap_mm3": knuckle_overlap,
                "total_support_body_overlap_mm3": total_overlap,
                "partition_volume_delta_mm3": partition_delta,
                "foot_positive_attachment": foot_overlap > CONTACT_EPS_MM3,
                "knuckle_positive_attachment": knuckle_overlap > CONTACT_EPS_MM3,
                "pass": (foot_overlap > CONTACT_EPS_MM3 and knuckle_overlap > CONTACT_EPS_MM3
                         and partition_delta < BODY_DIFF_TOL_MM3),
            }
            contact_state[label] = row
            if not row["pass"]:
                add_failure(report, "authorized_support_foot_and_knuckle_body_contact", state=state,
                            label=label, **row)
        contacts[state] = contact_state

        per_hardware = {}
        for label in (*SUPPORTS, PIN):
            pairs = [(f"A5:{name}", parts[label], parts[name]) for name in A5_LABELS
                     if not (label in SUPPORTS and name == BODY)]
            result = exact_minimum(pairs)
            result["pass"] = pass_clearance(result)
            per_hardware[label] = result
            if not result["pass"]:
                add_failure(report, "saved_fixed_hardware_to_A5_clearance_not_over_0_2_mm",
                            state=state, label=label, result=result)
        hardware_clearance[state] = per_hardware
    report["checks"]["saved_state_all_pair_interactions"] = interactions
    report["checks"]["authorized_support_body_contact"] = contacts
    report["checks"]["saved_fixed_hardware_clearance_to_A5"] = hardware_clearance

    # Compare all three saved states' new fixed hardware with R2 Stowed shifted
    # down, and check all within-tail hardware clearances (no body exception).
    fixed_pair_checks = {}
    if all(label in r3["Stowed"] for label in (*SUPPORTS, PIN)):
        pairs = [(f"{a}:{b}", r3["Stowed"][a], r3["Stowed"][b])
                 for index, a in enumerate((*SUPPORTS, PIN))
                 for b in (*SUPPORTS, PIN)[index + 1:]]
        fixed_pair_checks = exact_minimum(pairs)
        fixed_pair_checks["pass"] = pass_clearance(fixed_pair_checks)
        if not fixed_pair_checks["pass"]:
            add_failure(report, "fixed_hardware_mutual_clearance_not_over_0_2_mm", result=fixed_pair_checks)
    report["checks"]["fixed_hardware_mutual_clearance"] = fixed_pair_checks

    # Cross-check the saved R3 stowed fin against reconstructed A5 main-wing
    # poses, at the full 61-point uniform grid plus the five early samples.
    motion_rows = []
    motion_failures = []
    try:
        sys.path.insert(0, str(ROOT / "src"))
        import check_interleaved_a5 as a5check

        base = a5["Stowed"]
        needed = (*a5check.PANELS, *a5check.SUPPORTS)
        missing = sorted(set(needed) - set(base))
        if missing:
            raise RuntimeError(f"Saved A5 stowed input lacks motion-helper parts: {missing}")
        canonical = {
            label: a5check.panel_canonical(base[label], *label.split("_"),
                                          a5check.CUMULATIVE_A2_DROP_MM)
            for label in a5check.PANELS
        }
        stowed_parts = r3["Stowed"]
        for index, fraction in enumerate(FOLD_SAMPLES):
            posed_a5 = a5check.move_saved_stowed(
                base, fraction, canonical, a5check.CUMULATIVE_A2_DROP_MM)
            posed_a5[BODY] = stowed_parts[BODY]
            moving_fin = stowed_parts[FIN].rotate(IDENTITY_AXIS, FOLD_ANGLE_DEG * fraction)
            fin_pairs = [(f"fixed:{label}", moving_fin, stowed_parts[label])
                         for label in (*SUPPORTS, PIN)]
            fin_pairs.extend((f"A5:{label}", moving_fin, posed_a5[label]) for label in A5_LABELS)
            fin_result = exact_minimum(fin_pairs)
            fin_result["pass"] = pass_clearance(fin_result)

            hardware_results = {}
            for label in (*SUPPORTS, PIN):
                obstacles = [(f"A5:{name}", stowed_parts[label], posed_a5[name])
                             for name in A5_LABELS
                             if not (label in SUPPORTS and name == BODY)]
                result = exact_minimum(obstacles)
                result["pass"] = pass_clearance(result)
                hardware_results[label] = result

            row = {
                "sample": index, "fraction": fraction,
                "angle_deg": FOLD_ANGLE_DEG * fraction,
                "moving_saved_stowed_fin_vs_fixed_hardware_and_modified_A5": fin_result,
                "fixed_hardware_vs_reconstructed_A5_motion": hardware_results,
                "pass": fin_result["pass"] and all(v["pass"] for v in hardware_results.values()),
            }
            motion_rows.append(row)
            if not row["pass"]:
                motion_failures.append({"sample": index, "fraction": fraction, "details": row})
    except Exception as exc:
        add_failure(report, "saved_A5_motion_helper_crosscheck", error=repr(exc),
                    traceback=traceback.format_exc())

    fin_clearances = [row["moving_saved_stowed_fin_vs_fixed_hardware_and_modified_A5"]["minimum_clearance_mm"]
                      for row in motion_rows
                      if row["moving_saved_stowed_fin_vs_fixed_hardware_and_modified_A5"]["minimum_clearance_mm"] is not None]
    motion_summary = {
        "sample_count": len(motion_rows), "expected_sample_count": 66,
        "uniform_samples_count": 61, "early_samples": list(EARLY_FRACTIONS),
        "minimum_fin_clearance_mm": min(fin_clearances) if fin_clearances else None,
        "minimum_fin_clearance_witness": min(
            (row["moving_saved_stowed_fin_vs_fixed_hardware_and_modified_A5"] for row in motion_rows),
            key=lambda result: result["minimum_clearance_mm"]
            if result["minimum_clearance_mm"] is not None else math.inf,
        ).get("witness_pair") if motion_rows else None,
        "unexpected_overlaps_ge_0_001_mm3": [
            {"sample": row["sample"], "fraction": row["fraction"], **overlap}
            for row in motion_rows
            for result in [row["moving_saved_stowed_fin_vs_fixed_hardware_and_modified_A5"],
                           *row["fixed_hardware_vs_reconstructed_A5_motion"].values()]
            for overlap in result["unexpected_overlaps_ge_0_001_mm3"]
        ],
        "all_samples_pass": len(motion_rows) == 66 and not motion_failures,
        "continuous_sweep_proof": False,
    }
    if len(motion_rows) != 66:
        add_failure(report, "66_sample_motion_coverage", expected=66, actual=len(motion_rows))
    if motion_failures:
        add_failure(report, "66_sample_motion_clearance_or_overlap", failures=motion_failures)
    report["checks"]["saved_geometry_A5_motion_crosscheck"] = {
        "summary": motion_summary, "samples": motion_rows,
    }

    report["passed"] = not report["failures"]
    report["summary"] = {
        "passed": report["passed"], "failure_count": len(report["failures"]),
        "R3_saved_assemblies_imported": sum(bool(r3[state]) for state in STATES),
        "R3_component_count_each": len(R3_LABELS),
        "nonbody_A5_components_compared": sum(row["compared_count"] for row in base_identity.values()),
        "saved_R3_fin_pose_states_compared": len(pose_identity),
        "motion": motion_summary,
        "whole_assembly_conservative_YZ_envelopes_mm": {
            state: row.get("whole_assembly_conservative_YZ_envelope_mm")
            for state, row in cutter_checks["states"].items()},
        "stowed_tail_only_max_conservative_YZ_radius_mm":
            cutter_checks["states"].get("Stowed", {}).get("tail_only_max_conservative_YZ_radius_mm"),
        "body_isolated_expected_symdiff_mm3": pocket_identity.get("body_pocket_vs_A5_stowed_minus_cutters_mm3"),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), **report["summary"],
                      "failed_checks": [failure["check"] for failure in report["failures"]]}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        failure = {
            "gate": "TailR3_saved_geometry_validation", "units": "mm", "passed": False,
            "error": repr(exc), "traceback": traceback.format_exc(),
        }
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(REPORT_PATH), "passed": False, "error": repr(exc)}, indent=2))
        raise SystemExit(2)
