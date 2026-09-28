"""Saved-STEP validation for the clipped rear-fin R2 gate.

Inputs are only the saved R2, matching A5, and matching R1 Tall artifacts.
The checker performs no source-model rebuild and does not modify any input.
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
REPORT_PATH = ROOT / "reviews" / "tail_fin_r2_checks.json"
STATES = ("Stowed", "Midfold", "Deployed")
STATE_FRACTIONS = {"Stowed": 0.0, "Midfold": 0.5, "Deployed": 1.0}
FOLD_SAMPLES = tuple(i / 30.0 for i in range(31))
TAIL_LABELS = (
    "tail_r1_fin_root",
    "tail_r1_fixed_knuckle_aft",
    "tail_r1_fixed_knuckle_forward",
    "tail_r1_throughpin",
)
SUPPORT_LABELS = TAIL_LABELS[1:3]
BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
A5_LABELS = (
    BODY_LABEL,
    "port_carriage", "port_fixed_root", "port_front", "port_join", "port_rear",
    "starboard_carriage", "starboard_fixed_root", "starboard_front", "starboard_join", "starboard_rear",
    "supported_housing", "top_cover",
)
SHIFT_X = -80.0
HINGE_Y = 82.0
HINGE_Z = 88.5
FOLD_ANGLE_DEG = -135.0
BASE_TOL_MM3 = 0.01
R1_TAIL_TOL_MM3 = 0.01
STATE_TOL_MM3 = 0.01
OVERLAP_TOL_MM3 = 0.001
CONTACT_EPS_MM3 = 1.0e-5
CLEARANCE_MM = 0.2
RADIAL_LIMIT_MM = 125.0
BOUND_TOL_MM = 0.01
R2_PATHS = {s: ROOT / "STEP" / f"Q_Tail_R2_Clipped_{s}.step" for s in STATES}
A5_PATHS = {s: ROOT / "STEP" / f"O_Interleaved_A5_{s}.step" for s in STATES}
R1_PATHS = {s: ROOT / "STEP" / f"Q_Tail_R1_Tall_{s}.step" for s in STATES}
FOOT_X_RANGES = ((-1335.0, -1326.0), (-1084.0, -1075.0))
# Axial inner faces of the saved R1 Tall pin caps after the locked -80 mm
# translation; the complete R2 pin is also Boolean-compared against that STEP.
PIN_CAP_INNER_X = (-1335.3, -1074.7)
IDENTITY_AXIS = bd.Axis((0.0, HINGE_Y, HINGE_Z), (1.0, 0.0, 0.0))


def parts_from_step(path: Path):
    """Flatten the saved STEP assembly and preserve duplicate-label evidence."""
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
    duplicates = []
    for part in leaves:
        label = str(part.label)
        if label in parts:
            duplicates.append(label)
        parts[label] = part
    return parts, duplicates


def bbox(shape):
    box = shape.bounding_box(optimal=False)
    return ((float(box.min.X), float(box.min.Y), float(box.min.Z)),
            (float(box.max.X), float(box.max.Y), float(box.max.Z)))


def bbox_gap(a, b):
    alo, ahi = bbox(a)
    blo, bhi = bbox(b)
    gaps = [max(0.0, alo[i] - bhi[i], blo[i] - ahi[i]) for i in range(3)]
    return math.sqrt(sum(gap * gap for gap in gaps))


def radial_bound(shape):
    lo, hi = bbox(shape)
    return math.hypot(max(abs(lo[1]), abs(hi[1])), max(abs(lo[2]), abs(hi[2])))


def solid_metrics(shape):
    solids = list(shape.solids())
    volumes = [float(solid.volume) for solid in solids]
    return {
        "solid_count": len(solids),
        "positive_volumes_mm3": volumes,
        "valid": bool(shape.is_valid),
        "pass": bool(shape.is_valid and len(solids) == 1 and volumes and all(v > 0.0 for v in volumes)),
    }


def symdiff_volume(a, b):
    return float((a - b).volume) + float((b - a).volume)


def exact_pair_measure(a, b):
    overlap = float(overlap_volume(a, b))
    distance = float(closest_points(a, b).distance)
    return overlap, distance


def exact_minimum(pairs):
    """Find exact nearest pair with only rigorous disjoint-AABB pruning."""
    candidates = sorted((bbox_gap(a, b), name, a, b) for name, a, b in pairs)
    best = math.inf
    witness = None
    exact_count = 0
    pruned = 0
    overlaps = []
    for lower, name, first, second in candidates:
        if lower > best:
            pruned += 1
            continue
        overlap = float(overlap_volume(first, second))
        exact_count += 1
        distance = float(closest_points(first, second).distance)
        if overlap >= OVERLAP_TOL_MM3:
            overlaps.append({"pair": name, "overlap_mm3": overlap})
        if distance < best:
            best, witness = distance, name
    return {
        "minimum_clearance_mm": None if math.isinf(best) else best,
        "witness_pair": witness,
        "exact_pairs_tested": exact_count,
        "AABB_lower_bound_pairs_pruned": pruned,
        "overlaps_ge_0_001_mm3": overlaps,
    }


def add_failure(report, check, **details):
    report["failures"].append({"check": check, **details})


def read_inventory(path, expected_labels, report, key):
    if not path.is_file():
        add_failure(report, "required_saved_STEP_missing", artifact=key, path=str(path))
        return {}
    try:
        parts, duplicates = parts_from_step(path)
        missing = sorted(set(expected_labels) - set(parts))
        extra = sorted(set(parts) - set(expected_labels))
        topology = {label: solid_metrics(shape) for label, shape in parts.items()}
        report["saved_artifacts"][key] = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "part_count": len(parts),
            "expected_part_count": len(expected_labels),
            "labels": sorted(parts),
            "duplicate_labels": duplicates,
            "missing_labels": missing,
            "unexpected_labels": extra,
            "topology": topology,
        }
        if duplicates or missing or extra or len(parts) != len(expected_labels):
            add_failure(report, "saved_STEP_inventory", artifact=key, duplicate_labels=duplicates,
                        missing_labels=missing, unexpected_labels=extra, actual_count=len(parts),
                        expected_count=len(expected_labels))
        for label, metrics in topology.items():
            if not metrics["pass"]:
                add_failure(report, "saved_component_not_single_valid_positive_solid",
                            artifact=key, label=label, metrics=metrics)
        return parts
    except Exception as exc:
        add_failure(report, "saved_STEP_import", artifact=key, path=str(path), error=repr(exc),
                    traceback=traceback.format_exc())
        return {}


def main():
    report = {
        "gate": "rear_fin_R2_clipped_saved_validation",
        "units": "mm",
        "scope": "Saved R2/A5/R1 STEP validation only; no source rebuild or visual approval.",
        "thresholds": {
            "saved_A5_component_symmetric_difference_mm3_exclusive": BASE_TOL_MM3,
            "translated_R1_Tall_component_symmetric_difference_mm3_exclusive": R1_TAIL_TOL_MM3,
            "saved_fin_pose_symmetric_difference_mm3_exclusive": STATE_TOL_MM3,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "motion_clearance_mm_exclusive": CLEARANCE_MM,
            "foot_body_contact_mm3_exclusive": CONTACT_EPS_MM3,
            "stowed_tail_radial_bound_mm_exclusive": RADIAL_LIMIT_MM,
            "tail_root_X_bbox_expected_mm": [-1325.0, -1085.0],
            "hardware_union_X_bbox_expected_mm": [-1336.0, -1074.0],
            "bbox_endpoint_tolerance_mm": BOUND_TOL_MM,
            "fold_samples": list(FOLD_SAMPLES),
            "translation_mm": [SHIFT_X, 0.0, 0.0],
            "fold_axis": [[0.0, HINGE_Y, HINGE_Z], [1.0, 0.0, 0.0]],
            "fold_angle_deg": FOLD_ANGLE_DEG,
        },
        "saved_artifacts": {},
        "checks": {},
        "failures": [],
    }

    r2, a5, r1 = {}, {}, {}
    expected_r2 = set(A5_LABELS) | set(TAIL_LABELS)
    for state in STATES:
        r2[state] = read_inventory(R2_PATHS[state], expected_r2, report, f"R2_{state}")
        a5[state] = read_inventory(A5_PATHS[state], A5_LABELS, report, f"A5_{state}")
        # R1 Tall saved artifacts are complete 17-part assemblies; only their
        # four tail leaves are translated and compared below.
        r1[state] = read_inventory(R1_PATHS[state], expected_r2, report, f"R1_Tall_{state}")

    # Each saved R2 base component must be the exact corresponding saved A5 solid.
    base_identity = {}
    for state in STATES:
        row = {}
        for label in A5_LABELS:
            if label not in r2[state] or label not in a5[state]:
                continue
            try:
                delta = symdiff_volume(r2[state][label], a5[state][label])
                row[label] = delta
                if delta >= BASE_TOL_MM3:
                    add_failure(report, "saved_A5_component_not_boolean_identical", state=state,
                                label=label, symmetric_difference_mm3=delta)
            except Exception as exc:
                add_failure(report, "saved_A5_component_boolean_comparison", state=state,
                            label=label, error=repr(exc))
        base_identity[state] = {
            "component_count_compared": len(row),
            "expected_component_count": len(A5_LABELS),
            "maximum_symmetric_difference_mm3": max(row.values()) if row else None,
            "symmetric_difference_mm3_by_label": row,
            "pass": len(row) == len(A5_LABELS) and all(v < BASE_TOL_MM3 for v in row.values()),
        }
        if len(row) != len(A5_LABELS):
            add_failure(report, "saved_A5_component_comparison_coverage", state=state,
                        expected=len(A5_LABELS), actual=len(row))
    report["checks"]["A5_base_identity"] = base_identity

    # The complete four-part R2 tail must be the matching saved R1 Tall state
    # translated aft by exactly 80 mm.
    tail_identity = {}
    translated_reference = {}
    for state in STATES:
        row = {}
        for label in TAIL_LABELS:
            if label not in r2[state] or label not in r1[state]:
                continue
            try:
                expected = r1[state][label].translate((SHIFT_X, 0.0, 0.0))
                translated_reference[(state, label)] = expected
                delta = symdiff_volume(r2[state][label], expected)
                row[label] = delta
                if delta >= R1_TAIL_TOL_MM3:
                    add_failure(report, "R2_tail_not_boolean_identical_to_translated_R1_Tall",
                                state=state, label=label, symmetric_difference_mm3=delta)
            except Exception as exc:
                add_failure(report, "translated_R1_tail_boolean_comparison", state=state,
                            label=label, error=repr(exc))
        tail_identity[state] = {
            "component_count_compared": len(row),
            "expected_component_count": len(TAIL_LABELS),
            "maximum_symmetric_difference_mm3": max(row.values()) if row else None,
            "symmetric_difference_mm3_by_label": row,
            "pass": len(row) == len(TAIL_LABELS) and all(v < R1_TAIL_TOL_MM3 for v in row.values()),
        }
        if len(row) != len(TAIL_LABELS):
            add_failure(report, "translated_R1_tail_comparison_coverage", state=state,
                        expected=len(TAIL_LABELS), actual=len(row))
    report["checks"]["translated_R1_Tall_identity"] = tail_identity

    # Midfold/deployed fin geometry must be exactly the specified rigid pose of
    # the saved R2 stowed fin; all stationary hardware remains untransformed.
    pose_identity = {}
    if TAIL_LABELS[0] in r2["Stowed"]:
        stowed_fin = r2["Stowed"][TAIL_LABELS[0]]
        for state in STATES:
            current = r2[state].get(TAIL_LABELS[0])
            if current is None:
                continue
            expected = stowed_fin.rotate(IDENTITY_AXIS, FOLD_ANGLE_DEG * STATE_FRACTIONS[state])
            delta = symdiff_volume(current, expected)
            pose_identity[state] = {
                "fraction": STATE_FRACTIONS[state],
                "angle_deg": FOLD_ANGLE_DEG * STATE_FRACTIONS[state],
                "fin_symmetric_difference_mm3": delta,
                "pass": delta < STATE_TOL_MM3,
            }
            if delta >= STATE_TOL_MM3:
                add_failure(report, "saved_R2_fin_not_transformed_stowed_fin", state=state,
                            symmetric_difference_mm3=delta)
    report["checks"]["saved_fin_pose_identity"] = pose_identity
    if len(pose_identity) != len(STATES):
        add_failure(report, "saved_fin_pose_identity_coverage", expected=len(STATES),
                    actual=len(pose_identity))

    # Measure actual saved extents and stowed radius, rather than infer them
    # from the source generator or the R1 comparison alone.
    envelopes = {}
    for state in STATES:
        parts = r2[state]
        if not all(label in parts for label in TAIL_LABELS):
            continue
        root_bounds = bbox(parts[TAIL_LABELS[0]])
        hardware_bounds = [bbox(parts[label]) for label in TAIL_LABELS[1:]]
        hardware_x = [min(bounds[0][0] for bounds in hardware_bounds),
                      max(bounds[1][0] for bounds in hardware_bounds)]
        tail_x = {label: [bbox(parts[label])[0][0], bbox(parts[label])[1][0]] for label in TAIL_LABELS}
        radii = {label: radial_bound(parts[label]) for label in TAIL_LABELS}
        root_x = [root_bounds[0][0], root_bounds[1][0]]
        x_expected = max(abs(root_x[i] - (-1325.0 if i == 0 else -1085.0)) for i in range(2)) <= BOUND_TOL_MM
        hardware_expected = max(abs(hardware_x[i] - (-1336.0 if i == 0 else -1074.0))
                                for i in range(2)) <= BOUND_TOL_MM
        radius_pass = state != "Stowed" or max(radii.values()) < RADIAL_LIMIT_MM
        envelopes[state] = {
            "tail_root_X_bbox_mm": root_x,
            "hardware_union_X_bbox_mm": hardware_x,
            "tail_part_X_bbox_mm": tail_x,
            "stowed_tail_part_conservative_YZ_radius_mm": radii if state == "Stowed" else None,
            "root_bbox_matches_expected_within_tolerance": x_expected,
            "hardware_bbox_matches_expected_within_tolerance": hardware_expected,
            "stowed_radius_below_125_mm": radius_pass,
            "pass": x_expected and hardware_expected and radius_pass,
        }
        if not x_expected:
            add_failure(report, "saved_tail_root_X_bbox_mismatch", state=state,
                        measured_mm=root_x, expected_mm=[-1325.0, -1085.0], tolerance_mm=BOUND_TOL_MM)
        if not hardware_expected:
            add_failure(report, "saved_tail_hardware_X_bbox_mismatch", state=state,
                        measured_mm=hardware_x, expected_mm=[-1336.0, -1074.0], tolerance_mm=BOUND_TOL_MM)
        if not radius_pass:
            add_failure(report, "saved_stowed_tail_radius_not_below_125_mm", radii_mm=radii,
                        limit_mm=RADIAL_LIMIT_MM)
    report["checks"]["saved_tail_envelopes"] = envelopes

    # Only the two prescribed support feet may intersect the body. The actual
    # saved support is split by the locked foot envelope to measure the allowed
    # positive attachment separately from forbidden knuckle/body collision.
    body_contact = {}
    foot_and_knuckle = {}
    stowed = r2["Stowed"]
    if BODY_LABEL in stowed and all(label in stowed for label in SUPPORT_LABELS):
        body = stowed[BODY_LABEL]
        for label, (x0, x1) in zip(SUPPORT_LABELS, FOOT_X_RANGES):
            foot_region = bd.Solid.make_box(x1 - x0, 5.5, 8.5,
                                            plane=bd.Plane(origin=(x0, 79.0, 80.0)))
            support = stowed[label]
            foot = (support & foot_region).clean()
            knuckle = (support - foot_region).clean()
            foot_overlap = float(overlap_volume(foot, body))
            knuckle_overlap = float(overlap_volume(knuckle, body))
            combined_overlap = float(overlap_volume(support, body))
            row = {
                "foot_X_mm": [x0, x1],
                "foot_body_overlap_mm3": foot_overlap,
                "isolated_knuckle_body_overlap_mm3": knuckle_overlap,
                "combined_support_body_overlap_mm3": combined_overlap,
                "pass": (foot_overlap > CONTACT_EPS_MM3 and knuckle_overlap < OVERLAP_TOL_MM3
                         and abs(combined_overlap - foot_overlap) < BASE_TOL_MM3),
            }
            body_contact[label] = row
            if not row["pass"]:
                add_failure(report, "support_foot_positive_body_attachment_or_knuckle_clearance",
                            label=label, **row)
    if len(body_contact) != len(SUPPORT_LABELS):
        add_failure(report, "support_foot_contact_coverage", expected=len(SUPPORT_LABELS),
                    actual=len(body_contact))
    report["checks"]["authorized_foot_body_contacts"] = body_contact

    # Exact saved-state pair collision and stationary hardware clearance checks.
    # The only excluded body pair is each support/body pair already split above.
    saved_state_interactions = {}
    static_hardware_clearance = {}
    for state in STATES:
        parts = r2[state]
        base = a5[state]
        if not all(label in parts for label in TAIL_LABELS) or not all(label in base for label in A5_LABELS):
            continue
        unexpected = []
        exact_pair_count = 0
        for tail_label in TAIL_LABELS:
            for base_label in A5_LABELS:
                if tail_label in SUPPORT_LABELS and base_label == BODY_LABEL:
                    continue
                if bbox_gap(parts[tail_label], base[base_label]) > 0.0:
                    continue
                exact_pair_count += 1
                amount = float(overlap_volume(parts[tail_label], base[base_label]))
                if amount >= OVERLAP_TOL_MM3:
                    unexpected.append({"pair": [tail_label, base_label], "overlap_mm3": amount})
        for index, first in enumerate(TAIL_LABELS):
            for second in TAIL_LABELS[index + 1:]:
                if bbox_gap(parts[first], parts[second]) > 0.0:
                    continue
                exact_pair_count += 1
                amount = float(overlap_volume(parts[first], parts[second]))
                if amount >= OVERLAP_TOL_MM3:
                    unexpected.append({"pair": [first, second], "overlap_mm3": amount})
        state_row = {
            "AABB_intersecting_pairs_exactly_tested": exact_pair_count,
            "unexpected_overlaps_ge_0_001_mm3": unexpected,
            "pass": not unexpected,
        }
        saved_state_interactions[state] = state_row
        if unexpected:
            add_failure(report, "saved_state_unexpected_tail_A5_or_tail_mutual_overlap",
                        state=state, overlaps=unexpected)

        per_hardware = {}
        for label in (*SUPPORT_LABELS, TAIL_LABELS[3]):
            obstacles = [(f"A5:{name}", parts[label], base[name]) for name in A5_LABELS
                         if not (label in SUPPORT_LABELS and name == BODY_LABEL)]
            result = exact_minimum(obstacles)
            result["pass"] = (result["minimum_clearance_mm"] is not None
                              and result["minimum_clearance_mm"] > CLEARANCE_MM
                              and not result["overlaps_ge_0_001_mm3"])
            per_hardware[label] = result
            if not result["pass"]:
                add_failure(report, "saved_stationary_hardware_clearance_to_A5_not_over_0_2_mm",
                            state=state, label=label, result=result)
        static_hardware_clearance[state] = per_hardware
    report["checks"]["saved_state_interactions"] = saved_state_interactions
    report["checks"]["saved_stationary_hardware_vs_A5"] = static_hardware_clearance

    # Saved pin-to-bore radial fit plus the two measured cap/knuckle axial gaps.
    pin_fit = {}
    if all(label in stowed for label in TAIL_LABELS):
        pin = stowed[TAIL_LABELS[3]]
        radial_rows = []
        for label in TAIL_LABELS[:3]:
            overlap, distance = exact_pair_measure(pin, stowed[label])
            radial_rows.append({
                "pair": [TAIL_LABELS[3], label],
                "overlap_mm3": overlap,
                "surface_clearance_mm": distance,
                "pass": overlap < OVERLAP_TOL_MM3 and abs(distance - 0.25) < 1.0e-4,
            })
        aft_x = bbox(stowed[SUPPORT_LABELS[0]])
        forward_x = bbox(stowed[SUPPORT_LABELS[1]])
        # Cap inner faces are fixed by the measured matching R1 Tall shaft
        # envelope, translated by -80 mm; R2's complete pin is Boolean checked
        # against that saved reference above.
        cap_gaps = [aft_x[0][0] - PIN_CAP_INNER_X[0],
                    PIN_CAP_INNER_X[1] - forward_x[1][0]]
        pin_fit = {
            "nominal_radial_clearance_mm": 0.25,
            "pin_to_tail_surface_clearances": radial_rows,
            "measured_cap_to_knuckle_axial_gaps_mm": cap_gaps,
            "expected_cap_to_knuckle_axial_gap_mm": 0.3,
            "pass": (all(row["pass"] for row in radial_rows)
                     and all(abs(gap - 0.3) <= BOUND_TOL_MM for gap in cap_gaps)),
        }
        if not pin_fit["pass"]:
            add_failure(report, "saved_pin_radial_or_cap_axial_fit", metrics=pin_fit)
    else:
        add_failure(report, "saved_pin_fit_inputs_missing")
    report["checks"]["saved_pin_fit"] = pin_fit

    # Reconstruct each of the 31 A5 poses from the saved stowed STEP using the
    # same canonicalization/motion helper as the R1 checker and R2 probe.
    motion = {"fin_vs_stationary_hardware_and_A5": [], "stationary_hardware_vs_moving_A5": []}
    try:
        sys.path.insert(0, str(ROOT / "src"))
        import check_interleaved_a5 as a5check

        base = a5["Stowed"]
        required_a5 = (*a5check.PANELS, *a5check.SUPPORTS)
        missing = [label for label in required_a5 if label not in base]
        if missing:
            raise RuntimeError(f"Saved A5 stowed STEP lacks motion-helper parts: {missing}")
        canonical_panels = {}
        for label in a5check.PANELS:
            side, kind = label.split("_")
            canonical_panels[label] = a5check.panel_canonical(
                base[label], side, kind, a5check.CUMULATIVE_A2_DROP_MM)

        for sample_index, fraction in enumerate(FOLD_SAMPLES):
            posed_a5 = a5check.move_saved_stowed(
                base, fraction, canonical_panels, a5check.CUMULATIVE_A2_DROP_MM)
            absent = [label for label in A5_LABELS if label not in posed_a5]
            if absent:
                raise RuntimeError(f"A5 motion helper pose {sample_index} lacks parts: {absent}")
            moving_fin = stowed[TAIL_LABELS[0]].rotate(IDENTITY_AXIS, FOLD_ANGLE_DEG * fraction)
            obstacles = [(f"hardware:{label}", stowed[label]) for label in TAIL_LABELS[1:]]
            obstacles.extend((f"A5:{label}", posed_a5[label]) for label in A5_LABELS)
            fin_result = exact_minimum([(name, moving_fin, obstacle) for name, obstacle in obstacles])
            fin_result.update({"sample": sample_index, "fraction": fraction,
                               "angle_deg": FOLD_ANGLE_DEG * fraction,
                               "obstacle_pair_count": len(obstacles)})
            fin_result["pass"] = (fin_result["minimum_clearance_mm"] is not None
                                  and fin_result["minimum_clearance_mm"] > CLEARANCE_MM
                                  and not fin_result["overlaps_ge_0_001_mm3"])
            motion["fin_vs_stationary_hardware_and_A5"].append(fin_result)
            if not fin_result["pass"]:
                add_failure(report, "31_sample_fin_motion_clearance", sample=sample_index,
                            fraction=fraction, result=fin_result)

            hardware_results = {}
            for label in (*SUPPORT_LABELS, TAIL_LABELS[3]):
                pairs = [(f"A5:{name}", stowed[label], posed_a5[name]) for name in A5_LABELS
                         if not (label in SUPPORT_LABELS and name == BODY_LABEL)]
                result = exact_minimum(pairs)
                result["pass"] = (result["minimum_clearance_mm"] is not None
                                  and result["minimum_clearance_mm"] > CLEARANCE_MM
                                  and not result["overlaps_ge_0_001_mm3"])
                hardware_results[label] = result
                if not result["pass"]:
                    add_failure(report, "31_sample_stationary_hardware_vs_A5_motion_clearance",
                                sample=sample_index, fraction=fraction, label=label, result=result)
            motion["stationary_hardware_vs_moving_A5"].append({
                "sample": sample_index,
                "fraction": fraction,
                "parts": hardware_results,
                "pass": all(row["pass"] for row in hardware_results.values()),
            })
    except Exception as exc:
        add_failure(report, "A5_saved_stowed_motion_helper_crosscheck", error=repr(exc),
                    traceback=traceback.format_exc())

    fin_rows = motion["fin_vs_stationary_hardware_and_A5"]
    hardware_rows = motion["stationary_hardware_vs_moving_A5"]
    fin_clearances = [row["minimum_clearance_mm"] for row in fin_rows
                      if row["minimum_clearance_mm"] is not None]
    hardware_clearances = [result["minimum_clearance_mm"] for row in hardware_rows
                           for result in row["parts"].values()
                           if result["minimum_clearance_mm"] is not None]
    motion_summary = {
        "expected_sample_count": len(FOLD_SAMPLES),
        "fin_sample_count": len(fin_rows),
        "stationary_hardware_sample_count": len(hardware_rows),
        "minimum_fin_to_hardware_or_A5_clearance_mm": min(fin_clearances) if fin_clearances else None,
        "minimum_fin_witness": min(fin_rows, key=lambda row: row["minimum_clearance_mm"]
                                    if row["minimum_clearance_mm"] is not None else math.inf).get("witness_pair")
        if fin_rows else None,
        "minimum_stationary_hardware_to_A5_clearance_mm": min(hardware_clearances)
        if hardware_clearances else None,
        "fin_all_samples_pass": len(fin_rows) == len(FOLD_SAMPLES) and all(row["pass"] for row in fin_rows),
        "hardware_all_samples_pass": (len(hardware_rows) == len(FOLD_SAMPLES)
                                      and all(row["pass"] for row in hardware_rows)),
    }
    motion["summary"] = motion_summary
    report["checks"]["31_sample_saved_geometry_motion"] = motion
    if len(fin_rows) != len(FOLD_SAMPLES):
        add_failure(report, "31_sample_fin_motion_coverage", expected=len(FOLD_SAMPLES), actual=len(fin_rows))
    if len(hardware_rows) != len(FOLD_SAMPLES):
        add_failure(report, "31_sample_hardware_motion_coverage", expected=len(FOLD_SAMPLES), actual=len(hardware_rows))

    report["passed"] = not report["failures"]
    report["summary"] = {
        "passed": report["passed"],
        "failure_count": len(report["failures"]),
        "R2_saved_artifacts_imported": sum(bool(r2[state]) for state in STATES),
        "base_components_boolean_compared": sum(row["component_count_compared"]
                                                 for row in base_identity.values()),
        "translated_R1_tail_parts_boolean_compared": sum(row["component_count_compared"]
                                                         for row in tail_identity.values()),
        "tail_root_X_bbox_stowed_mm": envelopes.get("Stowed", {}).get("tail_root_X_bbox_mm"),
        "hardware_union_X_bbox_stowed_mm": envelopes.get("Stowed", {}).get("hardware_union_X_bbox_mm"),
        "maximum_stowed_tail_radius_mm": max(
            envelopes.get("Stowed", {}).get("stowed_tail_part_conservative_YZ_radius_mm", {}).values(),
            default=None),
        "foot_body_overlap_mm3": {label: row["foot_body_overlap_mm3"]
                                   for label, row in body_contact.items()},
        "knuckle_body_overlap_mm3": {label: row["isolated_knuckle_body_overlap_mm3"]
                                      for label, row in body_contact.items()},
        "pin_clearance_mm": {row["pair"][1]: row["surface_clearance_mm"]
                              for row in pin_fit.get("pin_to_tail_surface_clearances", [])},
        "cap_axial_gaps_mm": pin_fit.get("measured_cap_to_knuckle_axial_gaps_mm"),
        "motion": motion_summary,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), **report["summary"]}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
