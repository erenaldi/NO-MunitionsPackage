"""Saved-STEP validation for the one-corner rear-fin R1 gate.

Only exported Q_Tail_R1 artifacts and immutable saved A5 artifacts are inputs.
The independent solids below restate the locked brief dimensions; source model
factories are deliberately not called. The A5 saved-stowed motion helper is
used only to place the immutable A5 parts for tail/main-wing cross checks.
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
REPORT_PATH = ROOT / "reviews" / "tail_fin_r1_checks.json"
VARIANTS = ("Compact", "Swept", "Tall")
STATES = (("Stowed", 0.0), ("Midfold", 0.5), ("Deployed", 1.0))
FOLD_SAMPLES = tuple(i / 30.0 for i in range(31))

HINGE_Y = 82.0
HINGE_Z = 88.5
FOLD_ANGLE_DEG = -135.0
PANEL_Z = (87.0, 90.0)
ROOT_X = (-1245.0, -1005.0)
FIXED_X = ((-1255.0, -1246.0), (-1004.0, -995.0))
PIN_SHAFT_X = (-1255.3, -994.7)
CAP_X = ((-1256.0, -1255.3), (-994.7, -994.0))
BORE_R = 1.5
PIN_R = 1.25
KNUCKLE_R = 3.0
CAP_R = 2.5
FOOT_YZ = (79.0, 84.5, 80.0, 88.5)

PLANFORMS_V = {
    "Compact": ((-1245.0, 0.0), (-1005.0, 0.0), (-1105.0, 70.0), (-1210.0, 70.0)),
    "Swept": ((-1245.0, 0.0), (-1005.0, 0.0), (-1195.0, 90.0), (-1230.0, 90.0)),
    "Tall": ((-1245.0, 0.0), (-1005.0, 0.0), (-1100.0, 110.0), (-1200.0, 110.0)),
}

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
A5_STEPS = {state: ROOT / "STEP" / f"O_Interleaved_A5_{state}.step"
            for state, _ in STATES}
Q_STEPS = {
    (variant, state): ROOT / "STEP" / f"Q_Tail_R1_{variant}_{state}.step"
    for variant in VARIANTS for state, _ in STATES
}
BASE_TOL_MM3 = 0.01
GEOMETRY_TOL_MM3 = 0.01
OVERLAP_TOL_MM3 = 0.001
CONTACT_EPS_MM3 = 1.0e-5
CLEARANCE_MM = 0.2
RADIAL_LIMIT_MM = 125.0
X_LIMITS_MM = (-1400.0, 1400.0)
IDENTITY_AXIS = bd.Axis((0.0, HINGE_Y, HINGE_Z), (1.0, 0.0, 0.0))


def shape_volume(shape) -> float:
    return 0.0 if shape is None else float(shape.volume)


def symdiff_volume(a, b) -> float:
    return shape_volume(a - b) + shape_volume(b - a)


def bbox(shape):
    box = shape.bounding_box(optimal=False)
    return ((float(box.min.X), float(box.min.Y), float(box.min.Z)),
            (float(box.max.X), float(box.max.Y), float(box.max.Z)))


def bbox_gap(a, b) -> float:
    alo, ahi = bbox(a)
    blo, bhi = bbox(b)
    gaps = [max(0.0, alo[i] - bhi[i], blo[i] - ahi[i]) for i in range(3)]
    return math.sqrt(sum(gap * gap for gap in gaps))


def symmetric_radial_bound(shape) -> float:
    lo, hi = bbox(shape)
    return math.hypot(max(abs(lo[1]), abs(hi[1])), max(abs(lo[2]), abs(hi[2])))


def parts_from_step(path: Path):
    """Flatten saved assembly containers to labeled STEP leaves without deduping."""
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


def solid_metrics(shape):
    solids = list(shape.solids())
    volumes = [float(solid.volume) for solid in solids]
    return {
        "solid_count": len(solids),
        "positive_volumes_mm3": volumes,
        "valid": bool(shape.is_valid),
        "pass": bool(shape.is_valid and len(solids) == 1 and volumes and all(v > 0.0 for v in volumes)),
    }


def cylinder_x(radius, x0, x1, y=HINGE_Y, z=HINGE_Z):
    return bd.Cylinder(
        radius,
        x1 - x0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER),
    ).rotate(bd.Axis.Y, 90.0).translate(((x0 + x1) / 2.0, y, z))


def independent_fin(variant):
    points = [(x, HINGE_Y - v, PANEL_Z[0]) for x, v in PLANFORMS_V[variant]]
    panel = bd.extrude(
        bd.Face(bd.Wire.make_polygon(points, close=True)),
        amount=PANEL_Z[1] - PANEL_Z[0],
        dir=(0, 0, 1),
    )
    blank = (panel + cylinder_x(KNUCKLE_R, *ROOT_X)).clean()
    bore = cylinder_x(BORE_R, ROOT_X[0] - 0.1, ROOT_X[1] + 0.1)
    return (blank - bore).clean()


def independent_foot(x0, x1):
    y0, y1, z0, z1 = FOOT_YZ
    raw = bd.Solid.make_box(x1 - x0, y1 - y0, z1 - z0,
                            plane=bd.Plane(origin=(x0, y0, z0)))
    bore = cylinder_x(BORE_R, x0 - 0.1, x1 + 0.1)
    return (raw - bore).clean()


def independent_support(x0, x1):
    foot = bd.Solid.make_box(x1 - x0, FOOT_YZ[1] - FOOT_YZ[0], FOOT_YZ[3] - FOOT_YZ[2],
                             plane=bd.Plane(origin=(x0, FOOT_YZ[0], FOOT_YZ[2])))
    knuckle = cylinder_x(KNUCKLE_R, x0, x1)
    bore = cylinder_x(BORE_R, x0 - 0.1, x1 + 0.1)
    return (foot + knuckle - bore).clean()


def independent_pin():
    shaft = cylinder_x(PIN_R, *PIN_SHAFT_X)
    caps = [cylinder_x(CAP_R, x0, x1) for x0, x1 in CAP_X]
    return (shaft + caps[0] + caps[1]).clean()


def exact_pair_measure(a, b):
    overlap = float(overlap_volume(a, b))
    distance = float(closest_points(a, b).distance) if overlap <= OVERLAP_TOL_MM3 else 0.0
    return overlap, distance


def exact_minimum(pairs):
    """Exact nearest pair by AABB branch-and-bound; skipped pairs have a
    conservative lower bound strictly greater than the best exact distance."""
    candidates = sorted((bbox_gap(a, b), name, a, b) for name, a, b in pairs)
    best = math.inf
    witness = None
    exact_count = 0
    skipped = 0
    overlaps = []
    for lower, name, a, b in candidates:
        if lower > best:
            skipped += 1
            continue
        overlap = float(overlap_volume(a, b))
        exact_count += 1
        if overlap > OVERLAP_TOL_MM3:
            distance = 0.0
            overlaps.append({"pair": name, "overlap_mm3": overlap})
        else:
            distance = float(closest_points(a, b).distance)
            if overlap > 0.0:
                overlaps.append({"pair": name, "overlap_mm3": overlap, "below_overlap_limit": True})
        if distance < best:
            best = distance
            witness = name
    if math.isinf(best):
        return {"minimum_clearance_mm": None, "witness_pair": None,
                "exact_pairs_tested": exact_count, "AABB_lower_bound_pairs_pruned": skipped,
                "overlaps_over_0_001_mm3": overlaps}
    return {"minimum_clearance_mm": best, "witness_pair": witness,
            "exact_pairs_tested": exact_count, "AABB_lower_bound_pairs_pruned": skipped,
            "overlaps_over_0_001_mm3": overlaps}


def add_failure(report, check, **detail):
    report["failures"].append({"check": check, **detail})


def main():
    report = {
        "gate": "rear_fin_R1_saved_validation",
        "units": "mm",
        "thresholds": {
            "saved_A5_component_symmetric_difference_mm3_exclusive": BASE_TOL_MM3,
            "independent_tail_geometry_symmetric_difference_mm3_exclusive": GEOMETRY_TOL_MM3,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "motion_clearance_mm_exclusive": CLEARANCE_MM,
            "stowed_tail_radial_bound_mm_exclusive": RADIAL_LIMIT_MM,
            "tail_component_X_limits_mm_inclusive": list(X_LIMITS_MM),
            "fold_samples": list(FOLD_SAMPLES),
        },
        "inputs": {},
        "saved_artifacts": {},
        "checks": {},
        "failures": [],
    }

    all_paths = list(A5_STEPS.values()) + list(Q_STEPS.values())
    for path in all_paths:
        if not path.is_file():
            add_failure(report, "required_saved_STEP_missing", path=str(path))
            continue
        report["inputs"][path.name] = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    sys.path.insert(0, str(ROOT / "src"))
    try:
        import check_interleaved_a5 as a5check
    except Exception as exc:
        a5check = None
        add_failure(report, "A5_saved_stowed_motion_helper_import", error=repr(exc),
                    traceback=traceback.format_exc())

    a5_saved = {}
    for state, path in A5_STEPS.items():
        if not path.is_file():
            continue
        try:
            parts, duplicates = parts_from_step(path)
            a5_saved[state] = parts
            missing = sorted(set(A5_LABELS) - set(parts))
            extra = sorted(set(parts) - set(A5_LABELS))
            report["saved_artifacts"]["A5_" + state] = {
                "path": str(path), "part_count": len(parts), "labels": sorted(parts),
                "duplicate_labels": duplicates, "missing_labels": missing, "unexpected_labels": extra,
            }
            if duplicates or missing or extra or len(parts) != 13:
                add_failure(report, "A5_reference_inventory", state=state, duplicates=duplicates,
                            missing=missing, unexpected=extra, count=len(parts))
        except Exception as exc:
            a5_saved[state] = {}
            add_failure(report, "A5_reference_STEP_import", state=state, error=repr(exc),
                        traceback=traceback.format_exc())

    q_saved = {}
    for (variant, state), path in Q_STEPS.items():
        key = f"{variant}_{state}"
        if not path.is_file():
            continue
        try:
            parts, duplicates = parts_from_step(path)
            q_saved[(variant, state)] = parts
            expected_labels = set(A5_LABELS) | set(TAIL_LABELS)
            missing = sorted(expected_labels - set(parts))
            extra = sorted(set(parts) - expected_labels)
            metrics = {label: solid_metrics(part) for label, part in parts.items()}
            report["saved_artifacts"][key] = {
                "path": str(path), "part_count": len(parts), "expected_part_count": 17,
                "labels": sorted(parts), "duplicate_labels": duplicates,
                "missing_labels": missing, "unexpected_labels": extra,
                "topology": metrics,
            }
            if len(parts) != 17 or duplicates or missing or extra:
                add_failure(report, "Q_saved_artifact_inventory", variant=variant, state=state,
                            count=len(parts), duplicates=duplicates, missing=missing, unexpected=extra)
            for label, topology in metrics.items():
                if not topology["pass"]:
                    add_failure(report, "saved_component_not_single_valid_positive_solid",
                                variant=variant, state=state, label=label, metrics=topology)
        except Exception as exc:
            q_saved[(variant, state)] = {}
            add_failure(report, "Q_saved_STEP_import", variant=variant, state=state, path=str(path),
                        error=repr(exc), traceback=traceback.format_exc())

    # Compare each of the 13 saved A5 parts in every Q artifact with its
    # corresponding immutable saved A5 state using full 3D symmetric difference.
    base_identity = {}
    for (variant, state), qparts in q_saved.items():
        ref = a5_saved.get(state, {})
        row = {}
        for label in A5_LABELS:
            if label not in qparts or label not in ref:
                continue
            try:
                delta = symdiff_volume(qparts[label], ref[label])
                row[label] = delta
                if delta >= BASE_TOL_MM3:
                    add_failure(report, "saved_A5_component_not_boolean_identical",
                                variant=variant, state=state, label=label, symmetric_difference_mm3=delta)
            except Exception as exc:
                add_failure(report, "saved_A5_component_boolean_comparison", variant=variant,
                            state=state, label=label, error=repr(exc))
        base_identity[f"{variant}_{state}"] = {
            "component_count_compared": len(row), "maximum_symmetric_difference_mm3": max(row.values()) if row else None,
            "symmetric_difference_mm3_by_label": row,
        }
        if len(row) != 13:
            add_failure(report, "saved_A5_component_comparison_coverage", variant=variant, state=state,
                        expected=13, actual=len(row))
    report["checks"]["A5_base_identity"] = base_identity

    # Restate the brief's three polygon planforms and the shared hinge hardware
    # independently, then compare the saved stowed parts by Boolean volume.
    geometry_checks = {}
    try:
        independent_pin_shape = independent_pin()
        support_x_by_label = dict(zip(SUPPORT_LABELS, FIXED_X))
        for variant in VARIANTS:
            stowed = q_saved.get((variant, "Stowed"), {})
            entries = {}
            if all(label in stowed for label in TAIL_LABELS):
                expected_fin = independent_fin(variant)
                fin_delta = symdiff_volume(stowed[TAIL_LABELS[0]], expected_fin)
                entries[TAIL_LABELS[0]] = {
                    "planform_X_v_mm": [list(point) for point in PLANFORMS_V[variant]],
                    "planform_X_Y_mm_measured_coordinates": [[x, HINGE_Y - v] for x, v in PLANFORMS_V[variant]],
                    "panel_thickness_mm": PANEL_Z[1] - PANEL_Z[0],
                    "saved_vs_independent_fin_symmetric_difference_mm3": fin_delta,
                    "pass": fin_delta < GEOMETRY_TOL_MM3,
                }
                if fin_delta >= GEOMETRY_TOL_MM3:
                    add_failure(report, "saved_fin_does_not_match_brief_planform_and_root", variant=variant,
                                symmetric_difference_mm3=fin_delta)
                for label, xpair in support_x_by_label.items():
                    expected = independent_support(*xpair)
                    delta = symdiff_volume(stowed[label], expected)
                    entries[label] = {"saved_vs_independent_foot_knuckle_symmetric_difference_mm3": delta,
                                      "pass": delta < GEOMETRY_TOL_MM3}
                    if delta >= GEOMETRY_TOL_MM3:
                        add_failure(report, "saved_fixed_support_does_not_match_brief", variant=variant,
                                    label=label, symmetric_difference_mm3=delta)
                pin_delta = symdiff_volume(stowed[TAIL_LABELS[3]], independent_pin_shape)
                entries[TAIL_LABELS[3]] = {"saved_vs_independent_pin_symmetric_difference_mm3": pin_delta,
                                           "pass": pin_delta < GEOMETRY_TOL_MM3}
                if pin_delta >= GEOMETRY_TOL_MM3:
                    add_failure(report, "saved_pin_does_not_match_brief", variant=variant,
                                symmetric_difference_mm3=pin_delta)
            else:
                add_failure(report, "missing_tail_component_for_independent_dimension_check", variant=variant)
            geometry_checks[variant] = entries
    except Exception as exc:
        add_failure(report, "independent_brief_geometry_comparison", error=repr(exc),
                    traceback=traceback.format_exc())
    report["checks"]["brief_geometry"] = geometry_checks

    # Every state must carry exactly the same four solids after undoing only
    # the requested fin rotation. Hardware remains stationary.
    state_identity = {}
    for variant in VARIANTS:
        canonical = q_saved.get((variant, "Stowed"), {})
        for state, fraction in STATES:
            current = q_saved.get((variant, state), {})
            per_part = {}
            for label in TAIL_LABELS:
                if label not in canonical or label not in current:
                    continue
                try:
                    aligned = current[label]
                    if label == TAIL_LABELS[0]:
                        aligned = aligned.rotate(IDENTITY_AXIS, -FOLD_ANGLE_DEG * fraction)
                    delta = symdiff_volume(canonical[label], aligned)
                    per_part[label] = delta
                    if delta >= GEOMETRY_TOL_MM3:
                        add_failure(report, "tail_part_state_identity_after_inverse_fin_rotation",
                                    variant=variant, state=state, fraction=fraction, label=label,
                                    symmetric_difference_mm3=delta)
                except Exception as exc:
                    add_failure(report, "tail_part_state_identity_measurement", variant=variant,
                                state=state, label=label, error=repr(exc))
            state_identity[f"{variant}_{state}"] = {
                "fraction": fraction, "parts_compared": len(per_part),
                "symmetric_difference_mm3_by_part": per_part,
                "maximum_symmetric_difference_mm3": max(per_part.values()) if per_part else None,
            }
            if len(per_part) != 4:
                add_failure(report, "tail_part_state_identity_coverage", variant=variant, state=state,
                            expected=4, actual=len(per_part))
    report["checks"]["tail_state_identity"] = state_identity

    # Saved-state envelopes and interactions: all 17 parts stay inside the X
    # limits; the exclusive radial-125 constraint applies to the four new
    # stowed tail parts, not to the airframe's long-span saved A5 wings.
    envelope_checks = {}
    pair_overlap_checks = {}
    support_contacts = {}
    fixed_clearances = {}
    for (variant, state), parts in q_saved.items():
        if not parts:
            continue
        qkey = f"{variant}_{state}"
        state_env = {}
        for label, part in parts.items():
            lo, hi = bbox(part)
            radial = symmetric_radial_bound(part) if label in TAIL_LABELS else None
            state_env[label] = {"X_mm": [lo[0], hi[0]], "conservative_YZ_radius_mm": radial}
            # Apply this gate's X envelope to the four new tail solids. The
            # immutable A5 body is nominally +/-1400 and its imported STEP
            # bounding box carries OCC tolerance slop; its exact geometry is
            # independently Boolean-compared with the corresponding A5 file.
            if label in TAIL_LABELS and (lo[0] < X_LIMITS_MM[0] or hi[0] > X_LIMITS_MM[1]):
                add_failure(report, "saved_component_outside_X_limits", variant=variant, state=state,
                            label=label, bounds_X_mm=[lo[0], hi[0]], limits_mm=list(X_LIMITS_MM))
            if state == "Stowed" and label in TAIL_LABELS and radial >= RADIAL_LIMIT_MM:
                add_failure(report, "stowed_tail_part_outside_radius_125", variant=variant,
                            label=label, conservative_radius_mm=radial)
        envelope_checks[qkey] = {
            "component_count": len(parts),
            "X_limit_scope": "four new tail components; immutable A5 base is reported but not envelope-tested",
            "all_tail_X_within_limits": all(
                x["X_mm"][0] >= X_LIMITS_MM[0] and x["X_mm"][1] <= X_LIMITS_MM[1]
                for label, x in state_env.items() if label in TAIL_LABELS),
            "tail_stowed_maximum_conservative_radius_mm": (
                max((entry["conservative_YZ_radius_mm"] for label, entry in state_env.items()
                     if label in TAIL_LABELS), default=None) if state == "Stowed" else None),
            "per_component": state_env,
        }

        a5parts = a5_saved.get(state, {})
        unexpected = []
        tested = 0
        for tail_label in TAIL_LABELS:
            if tail_label not in parts:
                continue
            for base_label in A5_LABELS:
                if base_label not in a5parts:
                    continue
                lower = bbox_gap(parts[tail_label], a5parts[base_label])
                if lower > 0.0:
                    continue  # Disjoint AABBs prove zero overlap for this exact pair.
                tested += 1
                amount = float(overlap_volume(parts[tail_label], a5parts[base_label]))
                if tail_label in SUPPORT_LABELS and base_label == BODY_LABEL:
                    continue  # Explicit foot/body exception, separately measured below.
                if amount >= OVERLAP_TOL_MM3:
                    unexpected.append({"pair": [tail_label, base_label], "overlap_mm3": amount})
        for i, first in enumerate(TAIL_LABELS):
            if first not in parts:
                continue
            for second in TAIL_LABELS[i + 1:]:
                if second not in parts or bbox_gap(parts[first], parts[second]) > 0.0:
                    continue
                tested += 1
                amount = float(overlap_volume(parts[first], parts[second]))
                if amount >= OVERLAP_TOL_MM3:
                    unexpected.append({"pair": [first, second], "overlap_mm3": amount})
        pair_overlap_checks[qkey] = {
            "AABB_intersecting_pairs_exactly_tested": tested,
            "AABB_disjoint_pairs_proven_zero_overlap": 4 * 13 + 6 - tested,
            "unexpected_overlaps_ge_0_001_mm3": unexpected,
            "pass": not unexpected,
        }
        if unexpected:
            add_failure(report, "unexpected_tail_saved_A5_or_tail_part_overlap", variant=variant,
                        state=state, overlaps=unexpected)

        if state == "Stowed" and BODY_LABEL in a5parts:
            contact_rows = []
            for label, xpair in support_x_by_label.items():
                support = parts.get(label)
                if support is None:
                    continue
                foot = independent_foot(*xpair)
                foot_region = bd.Solid.make_box(xpair[1] - xpair[0], FOOT_YZ[1] - FOOT_YZ[0],
                                                FOOT_YZ[3] - FOOT_YZ[2],
                                                plane=bd.Plane(origin=(xpair[0], FOOT_YZ[0], FOOT_YZ[2])))
                actual_foot = (support & foot_region).clean()
                foot_identity = symdiff_volume(actual_foot, foot)
                isolated_knuckle = (support - foot).clean()
                foot_body_overlap = float(overlap_volume(foot, a5parts[BODY_LABEL]))
                knuckle_body_overlap = float(overlap_volume(isolated_knuckle, a5parts[BODY_LABEL]))
                support_body_overlap = float(overlap_volume(support, a5parts[BODY_LABEL]))
                row = {
                    "support_label": label,
                    "actual_foot_vs_probe_foot_symmetric_difference_mm3": foot_identity,
                    "foot_body_overlap_mm3": foot_body_overlap,
                    "isolated_knuckle_body_overlap_mm3": knuckle_body_overlap,
                    "combined_support_body_overlap_mm3": support_body_overlap,
                    "pass": (foot_identity < GEOMETRY_TOL_MM3 and foot_body_overlap > CONTACT_EPS_MM3
                             and knuckle_body_overlap < OVERLAP_TOL_MM3
                             and abs(support_body_overlap - foot_body_overlap) < GEOMETRY_TOL_MM3),
                }
                contact_rows.append(row)
                if not row["pass"]:
                    add_failure(report, "fixed_foot_body_support_or_isolated_knuckle_check",
                                variant=variant, details=row)
            support_contacts[variant] = contact_rows

        # Fixed hardware clearances against A5, except only foot/body support.
        if state == "Stowed":
            for label in (TAIL_LABELS[1], TAIL_LABELS[2], TAIL_LABELS[3]):
                part = parts.get(label)
                if part is None:
                    continue
                pairs = []
                for base_label in A5_LABELS:
                    if base_label not in a5parts or (label in SUPPORT_LABELS and base_label == BODY_LABEL):
                        continue
                    pairs.append((base_label, part, a5parts[base_label]))
                result = exact_minimum(pairs)
                result["pass"] = result["minimum_clearance_mm"] is not None and result["minimum_clearance_mm"] > CLEARANCE_MM
                fixed_clearances[f"{variant}:{label}"] = result
                if not result["pass"]:
                    add_failure(report, "fixed_tail_hardware_A5_clearance_not_over_0_2_mm",
                                variant=variant, label=label, result=result)

    report["checks"]["component_envelopes"] = envelope_checks
    report["checks"]["unexpected_overlaps"] = pair_overlap_checks
    report["checks"]["fixed_foot_contacts"] = support_contacts
    report["checks"]["fixed_hardware_A5_clearance"] = fixed_clearances

    # Verify saved hinge fit directly from STEP parts, not nominal radii alone.
    pin_fit = {}
    for variant in VARIANTS:
        parts = q_saved.get((variant, "Stowed"), {})
        if not all(label in parts for label in TAIL_LABELS):
            continue
        rows = []
        pin = parts[TAIL_LABELS[3]]
        for label in TAIL_LABELS[:3]:
            overlap, distance = exact_pair_measure(pin, parts[label])
            rows.append({"pair": [TAIL_LABELS[3], label], "overlap_mm3": overlap,
                         "surface_clearance_mm": distance,
                         "pass": overlap < OVERLAP_TOL_MM3 and abs(distance - 0.25) < 1.0e-4})
            if not rows[-1]["pass"]:
                add_failure(report, "saved_pin_to_bore_radial_fit", variant=variant,
                            pair=rows[-1]["pair"], overlap_mm3=overlap, clearance_mm=distance)
        pin_fit[variant] = {
            "nominal_bore_radius_mm": BORE_R, "nominal_pin_shaft_radius_mm": PIN_R,
            "nominal_radial_clearance_mm": BORE_R - PIN_R,
            "cap_radius_mm": CAP_R,
            "cap_to_knuckle_axial_gap_mm": [FIXED_X[0][0] - CAP_X[0][1], CAP_X[1][0] - FIXED_X[1][1]],
            "pin_to_saved_tail_clearance": rows,
            "pass": all(row["pass"] for row in rows),
        }
        if any(abs(gap - 0.3) > 1.0e-9 for gap in pin_fit[variant]["cap_to_knuckle_axial_gap_mm"]):
            pin_fit[variant]["pass"] = False
            add_failure(report, "brief_cap_knuckle_axial_gap", variant=variant,
                        gaps_mm=pin_fit[variant]["cap_to_knuckle_axial_gap_mm"])
    report["checks"]["pin_fit"] = pin_fit

    # Full 31-sample one-corner fin motion for every planform. Reconstruct the
    # A5 wing poses from saved stowed parts with the A5 checker helper and test
    # every AABB-near candidate; only pairs with a rigorous bound above the
    # current exact minimum are pruned from the nearest-distance calculation.
    motion_report = {}
    if a5check is not None and a5_saved.get("Stowed"):
        base = a5_saved["Stowed"]
        required_moving = (*a5check.PANELS, *a5check.SUPPORTS)
        canonical_panels = {}
        for label in a5check.PANELS:
            side, kind = label.split("_")
            if label in base:
                canonical_panels[label] = a5check.panel_canonical(
                    base[label], side, kind, a5check.CUMULATIVE_A2_DROP_MM)
        a5_motion = {}
        for fraction in FOLD_SAMPLES:
            try:
                posed = a5check.move_saved_stowed(
                    base, fraction, canonical_panels, a5check.CUMULATIVE_A2_DROP_MM)
                missing = [label for label in required_moving if label not in posed]
                if missing:
                    add_failure(report, "A5_saved_stowed_motion_helper_missing_parts",
                                fraction=fraction, missing=missing)
                a5_motion[fraction] = posed
            except Exception as exc:
                add_failure(report, "A5_saved_stowed_motion_pose_reconstruction", fraction=fraction,
                            error=repr(exc), traceback=traceback.format_exc())

        for variant in VARIANTS:
            stowed = q_saved.get((variant, "Stowed"), {})
            if TAIL_LABELS[0] not in stowed:
                continue
            sample_rows = []
            hardware_sample_rows = []
            for sample_index, fraction in enumerate(FOLD_SAMPLES):
                if fraction not in a5_motion:
                    continue
                moving_fin = stowed[TAIL_LABELS[0]].rotate(IDENTITY_AXIS, FOLD_ANGLE_DEG * fraction)
                a5_parts = a5_motion[fraction]
                obstacles = [(f"hardware:{label}", stowed[label])
                             for label in TAIL_LABELS[1:] if label in stowed]
                obstacles.extend((f"A5:{label}", a5_parts[label]) for label in A5_LABELS if label in a5_parts)
                pairs = [(name, moving_fin, obstacle) for name, obstacle in obstacles]
                result = exact_minimum(pairs)
                result.update({"sample": sample_index, "fraction": fraction,
                               "angle_deg": FOLD_ANGLE_DEG * fraction,
                               "obstacle_pair_count": len(pairs)})
                result["pass"] = (result["minimum_clearance_mm"] is not None
                                  and result["minimum_clearance_mm"] > CLEARANCE_MM
                                  and not result["overlaps_over_0_001_mm3"])
                if not result["pass"]:
                    add_failure(report, "31_sample_fin_motion_clearance", variant=variant,
                                sample=sample_index, fraction=fraction, result=result)

                # Also test the two stationary supports and through-pin against
                # the A5 parts moving at this same fraction. The only excluded
                # pair is each support's explicitly authorized foot/body
                # attachment; its isolated knuckle/body intersection is tested
                # independently above, and body remains static throughout.
                hardware_results = {}
                for hardware_label in TAIL_LABELS[1:]:
                    hardware = stowed[hardware_label]
                    pairs = [(f"A5:{base_label}", hardware, a5_parts[base_label])
                             for base_label in A5_LABELS
                             if base_label in a5_parts
                             and not (hardware_label in SUPPORT_LABELS and base_label == BODY_LABEL)]
                    hardware_result = exact_minimum(pairs)
                    hardware_result["pass"] = (
                        hardware_result["minimum_clearance_mm"] is not None
                        and hardware_result["minimum_clearance_mm"] > CLEARANCE_MM
                        and not hardware_result["overlaps_over_0_001_mm3"]
                    )
                    hardware_results[hardware_label] = hardware_result
                    if not hardware_result["pass"]:
                        add_failure(report, "31_sample_fixed_hardware_vs_A5_motion", variant=variant,
                                    sample=sample_index, fraction=fraction,
                                    hardware=hardware_label, result=hardware_result)
                hardware_sample_rows.append({
                    "sample": sample_index, "fraction": fraction,
                    "parts": hardware_results,
                    "pass": all(item["pass"] for item in hardware_results.values()),
                })
                result["stationary_hardware_vs_moving_A5"] = {
                    label: {key: value for key, value in measurement.items()
                            if key != "overlaps_over_0_001_mm3"}
                    for label, measurement in hardware_results.items()
                }
                sample_rows.append(result)
            clearances = [row["minimum_clearance_mm"] for row in sample_rows
                          if row["minimum_clearance_mm"] is not None]
            minimum_row = min(sample_rows, key=lambda row: row["minimum_clearance_mm"]
                              if row["minimum_clearance_mm"] is not None else math.inf) if sample_rows else None
            motion_report[variant] = {
                "sample_count": len(sample_rows), "expected_sample_count": 31,
                "obstacles_per_sample": len(TAIL_LABELS) - 1 + len(A5_LABELS),
                "minimum_sampled_clearance_mm": min(clearances) if clearances else None,
                "minimum_witness": (minimum_row.get("witness_pair") if minimum_row else None),
                "stationary_hardware_A5_sample_count": len(hardware_sample_rows),
                "stationary_hardware_A5_all_samples_pass": (
                    len(hardware_sample_rows) == 31
                    and all(row["pass"] for row in hardware_sample_rows)),
                "all_samples_pass": (len(sample_rows) == 31 and all(row["pass"] for row in sample_rows)
                                     and len(hardware_sample_rows) == 31
                                     and all(row["pass"] for row in hardware_sample_rows)),
                "stationary_hardware_A5_samples": hardware_sample_rows,
                "samples": sample_rows,
            }
            if len(sample_rows) != 31:
                add_failure(report, "31_sample_motion_coverage", variant=variant,
                            expected=31, actual=len(sample_rows))
            if len(hardware_sample_rows) != 31:
                add_failure(report, "31_sample_stationary_hardware_A5_coverage", variant=variant,
                            expected=31, actual=len(hardware_sample_rows))
    else:
        add_failure(report, "A5_saved_stowed_motion_reconstruction_unavailable")
    report["checks"]["fold_motion_vs_hardware_and_A5"] = motion_report

    report["passed"] = not report["failures"]
    report["summary"] = {
        "passed": report["passed"],
        "saved_Q_artifacts_imported": len(q_saved),
        "base_component_comparisons": sum(row["component_count_compared"]
                                           for row in base_identity.values()),
        "motion_samples": {variant: row.get("sample_count") for variant, row in motion_report.items()},
        "motion_min_clearance_mm": {variant: row.get("minimum_sampled_clearance_mm")
                                     for variant, row in motion_report.items()},
        "failure_count": len(report["failures"]),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT_PATH),
        **report["summary"],
        "unexpected_overlap_pair_failures": sum(len(row["unexpected_overlaps_ge_0_001_mm3"])
                                                 for row in pair_overlap_checks.values()),
        "foot_contact_metrics": support_contacts,
    }, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
