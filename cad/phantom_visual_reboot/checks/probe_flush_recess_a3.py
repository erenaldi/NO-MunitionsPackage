"""In-memory feasibility probe for the approved A2 flush-recess trial.

Reads the saved A2 stowed STEP, cuts only a trial well and four explicit layer
slots from its original body, and rigidly lowers every other saved component.
No source model, STEP, render, or design contract is rebuilt or modified.
"""
import itertools
import json
import math
import sys
from pathlib import Path

import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from interleaved_wing_a import LAYERS, pose  # noqa: E402
from joined_wing_r1 import pose as old_pose  # noqa: E402

SOURCE_STEP = ROOT / "STEP" / "O_Interleaved_A2_Stowed.step"
REPORT = ROOT / "reviews" / "flush_recess_a3_probe.json"
BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
DROP = 22.75
FLOOR_Z = 63.25
SLOT_RECTS = [
    {"name": "starboard_rear", "x": (-430.0, 530.0), "y": (-100.0, 100.0), "z": (65.7, 70.3)},
    {"name": "port_rear", "x": (-430.0, 530.0), "y": (-100.0, 100.0), "z": (71.2, 75.8)},
    {"name": "starboard_front", "x": (-430.0, 530.0), "y": (-100.0, 100.0), "z": (76.2, 80.8)},
    {"name": "port_front", "x": (-430.0, 530.0), "y": (-100.0, 100.0), "z": (81.7, 86.3)},
]
PANEL_LABELS = [side + "_" + kind for side in ("starboard", "port") for kind in ("rear", "front")]


def box(extents):
    x0, x1, y0, y1, z0, z1 = extents
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    )


def vol(shape):
    return 0.0 if shape is None else float(shape.volume)


def symdiff_volume(a, b):
    return vol(a - b) + vol(b - a)


def bounds(shape):
    b = shape.bounding_box()
    return {
        "x": [float(b.min.X), float(b.max.X)],
        "y": [float(b.min.Y), float(b.max.Y)],
        "z": [float(b.min.Z), float(b.max.Z)],
    }


def canonical(part, side, kind):
    if side == "port":
        part = part.mirror(bd.Plane.XZ)
    p = old_pose(0)
    x, y = p[kind]
    z = LAYERS[side][0 if kind == "rear" else 1]
    return part.translate((-x, -y + 5, -z)).rotate(bd.Axis.Z, -p[kind + "_angle"])


def moved(parts, fraction, canonical_panels):
    result = dict(parts)
    for side in ("port", "starboard"):
        for kind in ("front", "rear"):
            label = side + "_" + kind
            p = old_pose(fraction)
            z = LAYERS[side][0 if kind == "rear" else 1]
            panel = canonical_panels[label].rotate(bd.Axis.Z, p[kind + "_angle"])
            panel = panel.translate((p[kind][0], p[kind][1] - 5, z))
            if side == "port":
                panel = panel.mirror(bd.Plane.XZ)
            result[label] = panel
        start, end = pose(0, side), pose(fraction, side)
        for kind, key in (("carriage", "rear"), ("join", "joint")):
            dx = end[key][0] - start[key][0]
            dy = end[key][1] - start[key][1]
            result[side + "_" + kind] = parts[side + "_" + kind].translate((dx, dy, 0))
    return result


def overlap_data(a, b):
    gap = float(a.distance_to(b))
    overlap = vol(a & b) if gap < 0.001 else 0.0
    return gap, overlap


def main():
    report = {
        "source_step": str(SOURCE_STEP),
        "trial": {
            "all_nonbody_components_drop_mm": DROP,
            "well_extents_mm": {"x": [-450.3, 550.3], "y": [-74.3, 74.3], "z": [FLOOR_Z, 100.0]},
            "slots_mm": SLOT_RECTS,
            "floor_z_mm": FLOOR_Z,
            "no_automatic_widening": True,
        },
        "checks": {},
        "sample_results": [],
        "original_body_panel_intrusions": [],
        "failures": [],
    }
    failures = report["failures"]

    assembly = bd.import_step(SOURCE_STEP)
    source_parts = {p.label: p for p in assembly.children}
    if len(source_parts) != 12 or BODY_LABEL not in source_parts:
        raise RuntimeError("saved A2 STEP label/count mismatch: %r" % sorted(source_parts))
    report["checks"]["component_inventory"] = {
        "saved_part_count": len(source_parts),
        "retained_nonbody_count": len(source_parts) - 1,
        "retained_labels": sorted(source_parts),
        "nonbody_transform": [0.0, 0.0, -DROP],
    }
    original_body = source_parts[BODY_LABEL]
    if len(original_body.solids()) != 1:
        raise RuntimeError("saved source body is not one solid")

    well = box((-450.3, 550.3, -74.3, 74.3, FLOOR_Z, 100.0))
    cutters = well
    slot_shapes = {}
    for slot in SLOT_RECTS:
        x0, x1 = slot["x"]
        y0, y1 = slot["y"]
        z0, z1 = slot["z"]
        shape = box((x0, x1, y0, y1, z0, z1))
        slot_shapes[slot["name"]] = shape
        cutters = cutters + shape
    cutters = cutters.clean()

    recessed_body = (original_body - cutters).clean()
    body_bounds = bounds(original_body)
    recessed_bounds = bounds(recessed_body)
    outside_source = original_body - cutters
    outside_recessed = recessed_body - cutters
    outside_delta = symdiff_volume(outside_source, outside_recessed)
    removed_volume = vol(original_body) - vol(recessed_body)
    expected_removed = vol(original_body & cutters)
    body_valid = recessed_body.is_valid and len(recessed_body.solids()) == 1 and vol(recessed_body) > 0
    report["checks"]["body"] = {
        "source_valid_single_solid": original_body.is_valid and len(original_body.solids()) == 1,
        "recessed_valid_single_positive_solid": body_valid,
        "original_body_bounds_mm": body_bounds,
        "recessed_body_bounds_mm": recessed_bounds,
        "outside_cutter_symmetric_difference_mm3": outside_delta,
        "removed_volume_mm3": removed_volume,
        "source_intersection_cutter_volume_mm3": expected_removed,
        "removed_volume_error_mm3": abs(removed_volume - expected_removed),
    }
    if not body_valid:
        failures.append({"check": "recessed body topology", "valid": body_valid, "solids": len(recessed_body.solids())})
    if outside_delta > 0.01:
        failures.append({"check": "body identity outside cutters", "symmetric_difference_mm3": outside_delta})
    if abs(removed_volume - expected_removed) > 0.01:
        failures.append({"check": "body removed volume matches cutter union", "error_mm3": abs(removed_volume - expected_removed)})

    lowered = {
        label: (part if label == BODY_LABEL else part.translate((0, 0, -DROP)))
        for label, part in source_parts.items()
    }
    nonbody = {label: part for label, part in lowered.items() if label != BODY_LABEL}
    housing = nonbody["supported_housing"]
    housing_bounds = bounds(housing)
    floor_gap = float(housing.distance_to(recessed_body))
    floor_overlap = vol(housing & recessed_body) if floor_gap < 0.001 else 0.0
    report["checks"]["floor_seating"] = {
        "translated_housing_bounds_mm": housing_bounds,
        "requested_floor_z_mm": FLOOR_Z,
        "housing_bottom_z_error_mm": abs(housing_bounds["z"][0] - FLOOR_Z),
        "housing_to_body_gap_mm": floor_gap,
        "housing_body_overlap_mm3": floor_overlap,
    }
    if abs(housing_bounds["z"][0] - FLOOR_Z) > 0.001 or floor_gap > 0.001 or floor_overlap > 0.001:
        failures.append({"check": "housing floor seat", "bounds_z": housing_bounds["z"], "gap_mm": floor_gap, "overlap_mm3": floor_overlap})

    # Internal support path remains rigidly connected after the approved drop.
    support_contacts = []
    for label in ["starboard_fixed_root", "starboard_carriage", "port_fixed_root", "port_carriage"]:
        gap = float(nonbody[label].distance_to(housing))
        support_contacts.append({"part": label, "housing_gap_mm": gap})
        if gap > 0.001:
            failures.append({"check": "housing support path", "part": label, "gap_mm": gap})
    report["checks"]["support_path"] = support_contacts

    # Expected translated datum heights and the existing radial stowed envelope.
    panel_tops = {label: bounds(nonbody[label])["z"][1] for label in PANEL_LABELS}
    hardware_tops = {
        label: bounds(nonbody[label])["z"][1]
        for label in ("starboard_fixed_root", "starboard_carriage", "starboard_join", "port_fixed_root", "port_carriage", "port_join")
    }
    max_panel_top = max(panel_tops.values())
    max_hardware_top = max(hardware_tops.values())
    radial = {}
    for label, part in lowered.items():
        b = part.bounding_box()
        radial[label] = math.hypot(max(abs(b.min.Y), abs(b.max.Y)), max(abs(b.min.Z), abs(b.max.Z)))
    max_radial = max(radial.values())
    report["checks"]["stowed_datums_envelope"] = {
        "panel_top_z_mm_by_label": panel_tops,
        "uppermost_panel_top_z_mm": max_panel_top,
        "hardware_top_z_mm_by_label": hardware_tops,
        "uppermost_hinge_hardware_top_z_mm": max_hardware_top,
        "radial_bound_mm_by_label": radial,
        "complete_stowed_radial_bound_mm": max_radial,
        "radial_limit_mm_exclusive": 125.0,
    }
    if abs(max_panel_top - 86.0) > 0.001:
        failures.append({"check": "uppermost panel flush datum", "expected_z_mm": 86.0, "actual_z_mm": max_panel_top})
    if abs(max_hardware_top - 86.75) > 0.001:
        failures.append({"check": "hinge cap proud datum", "expected_z_mm": 86.75, "actual_z_mm": max_hardware_top})
    if max_radial >= 125.0:
        failures.append({"check": "stowed radial envelope", "actual_mm": max_radial, "limit_mm_exclusive": 125.0})

    canonical_panels = {label: canonical(source_parts[label], label.split("_")[0], label.split("_")[1]) for label in PANEL_LABELS}
    min_panel_clearance = {label: (float("inf"), None) for label in PANEL_LABELS}
    max_hardware_overlap = {"overlap_mm3": 0.0, "fraction": None, "part": None}
    original_intrusions = []
    for i in range(21):
        fraction = i / 20
        sample = moved(source_parts, fraction, canonical_panels)
        sample = {label: (part if label == BODY_LABEL else part.translate((0, 0, -DROP))) for label, part in sample.items()}
        sample_panels = {}
        sample_clearance = {}
        for label in PANEL_LABELS:
            panel = sample[label]
            gap = float(panel.distance_to(recessed_body))
            sample_clearance[label] = gap
            previous = min_panel_clearance[label]
            if gap < previous[0]:
                min_panel_clearance[label] = (gap, fraction)
            if gap <= 0.2:
                overlap = vol(panel & recessed_body) if gap < 0.001 else 0.0
                failures.append({"check": "panel-body clearance", "fraction": fraction, "panel": label, "gap_mm": gap, "overlap_mm3": overlap})
            sample_panels[label] = panel

            # Map any original-body intrusion to the fixed, approved trial cutters;
            # residual intrusion is evidence for the primary, not an auto-widening.
            source_gap, source_overlap = overlap_data(panel, original_body)
            if source_overlap > 0.001:
                intrusion = panel & original_body
                residual = intrusion - cutters
                residual_volume = vol(residual)
                intr = {
                    "fraction": fraction,
                    "panel": label,
                    "source_body_overlap_mm3": source_overlap,
                    "source_overlap_bounds_mm": bounds(intrusion),
                    "outside_trial_cutter_mm3": residual_volume,
                }
                if residual_volume > 0.001:
                    intr["required_additional_opening_bounds_mm"] = bounds(residual)
                original_intrusions.append(intr)

        hardware_names = [name for name in sample if name not in (BODY_LABEL, "supported_housing", *PANEL_LABELS)]
        body_pairs = []
        for label in hardware_names:
            gap, overlap = overlap_data(sample[label], recessed_body)
            body_pairs.append({"part": label, "gap_mm": gap, "overlap_mm3": overlap})
            if overlap > 0.001:
                if overlap > max_hardware_overlap["overlap_mm3"]:
                    max_hardware_overlap = {"overlap_mm3": overlap, "fraction": fraction, "part": label}
                failures.append({"check": "unexpected hardware-body overlap", "fraction": fraction, "part": label, "overlap_mm3": overlap, "gap_mm": gap})
        if fraction in (0.0, 0.5, 1.0):
            report["sample_results"].append({
                "fraction": fraction,
                "panel_body_clearance_mm": sample_clearance,
                "hardware_body_pairs": body_pairs,
            })

    report["checks"]["motion"] = {
        "law_source": "joined_wing_r1.pose via src/interleaved_wing_a.py; original rigid-transform sample logic",
        "sample_count": 21,
        "fractions": [i / 20 for i in range(21)],
        "minimum_panel_body_clearance_mm_by_label": {k: v[0] for k, v in min_panel_clearance.items()},
        "minimum_panel_clearance_sample_by_label": {k: v[1] for k, v in min_panel_clearance.items()},
        "worst_hardware_body_overlap": max_hardware_overlap,
        "hardware_body_tested_at_all_samples": True,
        "panel_body_clearance_limit_mm_exclusive": 0.2,
    }
    report["original_body_panel_intrusions"] = original_intrusions
    swept_extents = {}
    for label in PANEL_LABELS:
        hits = [item["source_overlap_bounds_mm"] for item in original_intrusions if item["panel"] == label]
        if hits:
            swept_extents[label] = {
                axis: [min(b[axis][0] for b in hits), max(b[axis][1] for b in hits)]
                for axis in ("x", "y", "z")
            }
    report["original_body_sweep_intrusion_bounds_mm_by_panel"] = swept_extents
    report["required_opening_extents_from_residual_intrusions_mm"] = [
        {"fraction": item["fraction"], "panel": item["panel"], "bounds": item["required_additional_opening_bounds_mm"], "residual_mm3": item["outside_trial_cutter_mm3"]}
        for item in original_intrusions if item["outside_trial_cutter_mm3"] > 0.001
    ]

    report["passed"] = not failures
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed": report["passed"],
        "report": str(REPORT),
        "body_valid_single_solid": body_valid,
        "outside_cutter_body_delta_mm3": outside_delta,
        "floor_gap_mm": floor_gap,
        "upper_panel_top_mm": max_panel_top,
        "upper_hinge_hardware_top_mm": max_hardware_top,
        "stowed_radial_bound_mm": max_radial,
        "minimum_panel_clearance_mm": report["checks"]["motion"]["minimum_panel_body_clearance_mm_by_label"],
        "additional_opening_count": len(report["required_opening_extents_from_residual_intrusions_mm"]),
        "failures": failures,
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
