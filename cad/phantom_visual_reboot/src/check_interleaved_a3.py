"""Saved-artifact validation for the A3 recessed interleaved-wing gate.

This checker reads saved A3 and A2 STEP artifacts only.  The A3 well and slot
dimensions below are independently restated from checks/probe_flush_recess_a3.py;
they are deliberately not imported from the A3 generator.
"""
import itertools
import json
import math
from pathlib import Path
import sys
import traceback

import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from interleaved_wing_a import LAYERS, pose  # noqa: E402
from joined_wing_r1 import pose as old_pose  # noqa: E402


BODY = "RDM9_R7_symmetric_body_20mm_wedge_R4"
HOUSING = "supported_housing"
DROP_MM = 22.75
BODY_TOL_MM3 = 0.01
OVERLAP_TOL_MM3 = 0.001
PANEL_CLEARANCE_MIN_MM = 0.2
CONTACT_TOL_MM = 0.001
WELL_EXTENTS_MM = (-450.3, 550.3, -74.3, 74.3, 63.25, 100.0)
SLOT_EXTENTS_MM = (
    (-430.0, 530.0, -100.0, 100.0, 65.7, 70.3),
    (-430.0, 530.0, -100.0, 100.0, 71.2, 75.8),
    (-430.0, 530.0, -100.0, 100.0, 76.2, 80.8),
    (-430.0, 530.0, -100.0, 100.0, 81.7, 86.3),
)
PANELS = tuple(
    side + "_" + kind
    for side in ("starboard", "port")
    for kind in ("rear", "front")
)
SUPPORTS = tuple(
    side + "_" + kind
    for side in ("starboard", "port")
    for kind in ("fixed_root", "carriage")
)
CAP_PARTS = tuple(
    side + "_" + kind
    for side in ("starboard", "port")
    for kind in ("fixed_root", "carriage", "join")
)
FULL_STATES = ("Stowed", "Midfold", "Deployed")
A3_PATHS = {
    "Stowed": ROOT / "STEP/O_Interleaved_A3_Stowed.step",
    "Module_Stowed": ROOT / "STEP/O_Interleaved_A3_Module_Stowed.step",
    "Midfold": ROOT / "STEP/O_Interleaved_A3_Midfold.step",
    "Deployed": ROOT / "STEP/O_Interleaved_A3_Deployed.step",
    "Body_Pocket": ROOT / "STEP/O_Interleaved_A3_Body_Pocket.step",
}
A2_PATHS = {
    state: ROOT / ("STEP/O_Interleaved_A2_" + state + ".step")
    for state in ("Stowed", "Module_Stowed", "Midfold", "Deployed")
}
REPORT_PATH = ROOT / "reviews/interleaved_a3_checks.json"


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


def symmetric_difference_volume(a, b):
    return volume(a - b) + volume(b - a)


def make_box(extents):
    x0, x1, y0, y1, z0, z1 = extents
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    )


def bounds(shape):
    b = shape.bounding_box()
    return {
        "x": [float(b.min.X), float(b.max.X)],
        "y": [float(b.min.Y), float(b.max.Y)],
        "z": [float(b.min.Z), float(b.max.Z)],
    }


def solid_valid(shape):
    return bool(shape.is_valid and len(shape.solids()) == 1 and volume(shape) > 0)


def parts_from_step(path):
    imported = bd.import_step(path)
    children = list(imported.children)
    if not children:
        children = [imported]
    result = {}
    duplicates = []
    for part in children:
        label = str(part.label)
        if label in result:
            duplicates.append(label)
        result[label] = part
    return result, duplicates


def canonical_a3_panel(part, side, kind):
    """Restore A3 saved panel to the A2 canonical frame for motion sampling."""
    part = part.translate((0, 0, DROP_MM))
    if side == "port":
        part = part.mirror(bd.Plane.XZ)
    p = old_pose(0)
    x, y = p[kind]
    z = LAYERS[side][0 if kind == "rear" else 1]
    return part.translate((-x, -y + 5, -z)).rotate(bd.Axis.Z, -p[kind + "_angle"])


def moved_a3_stowed(base, fraction, canonical_panels):
    """Rigidly move the saved A3 stowed parts using the approved A2 motion law."""
    result = dict(base)
    for side in ("starboard", "port"):
        p = old_pose(fraction)
        for kind in ("front", "rear"):
            label = side + "_" + kind
            z = LAYERS[side][0 if kind == "rear" else 1] - DROP_MM
            panel = canonical_panels[label].rotate(bd.Axis.Z, p[kind + "_angle"])
            panel = panel.translate((p[kind][0], p[kind][1] - 5, z))
            if side == "port":
                panel = panel.mirror(bd.Plane.XZ)
            result[label] = panel
        start, end = pose(0, side), pose(fraction, side)
        for kind, key in (("carriage", "rear"), ("join", "joint")):
            dx = end[key][0] - start[key][0]
            dy = end[key][1] - start[key][1]
            result[side + "_" + kind] = base[side + "_" + kind].translate((dx, dy, 0))
    return result


def main():
    report = {
        "artifact_prefix": "O_Interleaved_A3",
        "scope": (
            "five saved A3 STEP artifacts; exact A2 cutter/translation identity; "
            "saved topology, datums, contacts, and 21 simultaneous rigid-motion "
            "samples. Continuous sweep, strength, actuation, locks, and rack are unverified."
        ),
        "thresholds": {
            "body_identity_mm3_exclusive": BODY_TOL_MM3,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "panel_clearance_mm_exclusive": PANEL_CLEARANCE_MIN_MM,
            "contact_gap_mm_inclusive": CONTACT_TOL_MM,
            "nonbody_translation_mm": [0.0, 0.0, -DROP_MM],
        },
        "independent_cutters_mm": {
            "well": list(WELL_EXTENTS_MM),
            "slots": [list(s) for s in SLOT_EXTENTS_MM],
        },
        "artifacts": {},
        "body_cut_comparison": {},
        "state_identity": {},
        "panel_geometry_identity": {},
        "stowed": {},
        "contacts": {},
        "saved_pose_identity": {},
        "motion_samples": [],
        "intentional_overlap_exemptions": [
            [HOUSING, "starboard_fixed_root"],
            [HOUSING, "port_fixed_root"],
        ],
        "failures": [],
    }
    failures = report["failures"]

    def fail(check, **detail):
        failures.append({"check": check, **detail})

    try:
        a3 = {}
        for state, path in A3_PATHS.items():
            try:
                parts, duplicates = parts_from_step(path)
                a3[state] = parts
                report["artifacts"][state] = {
                    "path": str(path),
                    "labels": sorted(parts),
                    "part_count": len(parts),
                    "duplicate_labels": duplicates,
                }
                if duplicates:
                    fail("duplicate A3 labels", state=state, labels=duplicates)
            except Exception as exc:
                fail("A3 STEP import", state=state, path=str(path), error=repr(exc))
                a3[state] = {}

        a2 = {}
        for state, path in A2_PATHS.items():
            try:
                parts, duplicates = parts_from_step(path)
                a2[state] = parts
                if duplicates:
                    fail("duplicate A2 labels", state=state, labels=duplicates)
            except Exception as exc:
                fail("A2 reference STEP import", state=state, path=str(path), error=repr(exc))
                a2[state] = {}

        full = a3.get("Stowed", {})
        module = a3.get("Module_Stowed", {})
        if len(full) != 12:
            fail("full stowed part count", expected=12, actual=len(full))
        if len(module) != 11:
            fail("module stowed part count", expected=11, actual=len(module))
        if BODY not in full:
            fail("stowed body label missing", label=BODY)
        if set(module) != set(full) - {BODY}:
            fail("module/full label mismatch", differing=sorted(set(module) ^ (set(full) - {BODY})))

        # Validate topology across every saved A3 STEP and both stowed inventories.
        topology = {}
        for state, parts in a3.items():
            target_count = 11 if state == "Module_Stowed" else (1 if state == "Body_Pocket" else 12)
            if len(parts) != target_count:
                fail("saved artifact part count", state=state, expected=target_count, actual=len(parts))
            for label, part in parts.items():
                try:
                    valid = solid_valid(part)
                    count = len(part.solids())
                    v = volume(part)
                    topology[state + ":" + label] = {
                        "valid_single_positive_solid": valid,
                        "solid_count": count,
                        "volume_mm3": v,
                    }
                    if not valid:
                        fail("saved part topology", state=state, label=label, solid_count=count, volume_mm3=v)
                except Exception as exc:
                    topology[state + ":" + label] = {"error": repr(exc)}
                    fail("saved part topology measurement", state=state, label=label, error=repr(exc))
        report["topology"] = topology

        # Independent exact union from probe dimensions, then compare saved body.
        a2_stowed = a2.get("Stowed", {})
        a2_body = a2_stowed.get(BODY)
        saved_body = full.get(BODY)
        cutters = make_box(WELL_EXTENTS_MM)
        for slot in SLOT_EXTENTS_MM:
            cutters = cutters + make_box(slot)
        cutters = cutters.clean()
        if a2_body is not None and saved_body is not None:
            expected_body = (a2_body - cutters).clean()
            expected_body_valid = solid_valid(expected_body)
            expected_volume = volume(expected_body)
            body_delta = symmetric_difference_volume(saved_body, expected_body)
            outside_delta = symmetric_difference_volume(a2_body - cutters, saved_body - cutters)
            added_volume = volume(saved_body - a2_body)
            removed_volume = volume(a2_body - saved_body)
            expected_removed = volume(a2_body & cutters)
            removed_volume_error = abs(removed_volume - expected_removed)
            actual_bounds = bounds(saved_body)
            report["body_cut_comparison"] = {
                "source": str(A2_PATHS["Stowed"]),
                "expected_body_valid_single_positive_solid": expected_body_valid,
                "saved_body_valid_single_positive_solid": solid_valid(saved_body),
                "saved_vs_exact_cut_expected_symmetric_difference_mm3": body_delta,
                "outside_cut_symmetric_difference_mm3": outside_delta,
                "added_material_vs_A2_mm3": added_volume,
                "removed_material_vs_A2_mm3": removed_volume,
                "expected_intersection_with_cutter_union_mm3": expected_removed,
                "removed_volume_error_mm3": removed_volume_error,
                "saved_body_bounds_mm": actual_bounds,
                "body_remaining_roof_top_z_mm": actual_bounds["z"][1],
                "expected_roof_top_z_mm": 86.0,
                "expected_body_volume_mm3": expected_volume,
            }
            if not expected_body_valid:
                fail("expected cut body topology", valid=expected_body_valid)
            if body_delta > BODY_TOL_MM3:
                fail("saved body differs from exact A2 body-minus-cutters", difference_mm3=body_delta)
            if outside_delta > BODY_TOL_MM3:
                fail("body changed outside exact cutters", symmetric_difference_mm3=outside_delta)
            if added_volume > BODY_TOL_MM3:
                fail("added material relative to A2 body", volume_mm3=added_volume)
            if removed_volume_error > BODY_TOL_MM3:
                fail("removed material differs from cutter intersection", error_mm3=removed_volume_error)
            if abs(actual_bounds["z"][1] - 86.0) > 0.001:
                fail("body remaining roof datum", expected_z_mm=86.0, actual_z_mm=actual_bounds["z"][1])
        else:
            fail("body cut comparison unavailable", has_a2_body=a2_body is not None, has_saved_body=saved_body is not None)

        # Pocket is a standalone saved body and is identical to the full stowed body.
        pocket = a3.get("Body_Pocket", {})
        pocket_shape = pocket.get(BODY)
        if pocket_shape is None and len(pocket) == 1:
            pocket_shape = next(iter(pocket.values()))
        if pocket_shape is not None and saved_body is not None:
            pocket_delta = symmetric_difference_volume(pocket_shape, saved_body)
            report["body_cut_comparison"]["body_pocket_vs_full_stowed_mm3"] = pocket_delta
            if pocket_delta > BODY_TOL_MM3:
                fail("Body_Pocket differs from full stowed body", difference_mm3=pocket_delta)
        else:
            fail("Body_Pocket body unavailable", labels=sorted(pocket))

        # All matched saved A3 poses are exact A2 geometry translated -22.75 Z.
        for state, a2_parts in a2.items():
            a3_parts = a3.get(state, {})
            deltas = {}
            if not a2_parts or not a3_parts:
                report["state_identity"][state] = {"available": False}
                continue
            if set(a2_parts) != set(a3_parts):
                missing = sorted(set(a2_parts) - set(a3_parts))
                extra = sorted(set(a3_parts) - set(a2_parts))
                fail("A2/A3 labels differ", state=state, missing=missing, extra=extra)
            for label in sorted(set(a2_parts) & set(a3_parts)):
                if label == BODY:
                    if state == "Module_Stowed":
                        continue
                    continue  # Recessed body is checked against the exact cutter union above.
                try:
                    moved = a2_parts[label].translate((0, 0, -DROP_MM))
                    delta = symmetric_difference_volume(a3_parts[label], moved)
                    deltas[label] = delta
                    if delta > BODY_TOL_MM3:
                        fail("nonbody saved pose is not A2 translated exactly", state=state, label=label, difference_mm3=delta)
                except Exception as exc:
                    fail("nonbody A2/A3 pose comparison", state=state, label=label, error=repr(exc))
            report["state_identity"][state] = {
                "nonbody_translation_mm": [0.0, 0.0, -DROP_MM],
                "nonbody_symmetric_difference_mm3": deltas,
                "maximum_difference_mm3": max(deltas.values()) if deltas else None,
            }

        if set(module) == set(full) - {BODY}:
            identity = {}
            for label in sorted(module):
                try:
                    delta = symmetric_difference_volume(module[label], full[label])
                    identity[label] = delta
                    if delta > BODY_TOL_MM3:
                        fail("module/full stowed geometry differs", label=label, difference_mm3=delta)
                except Exception as exc:
                    fail("module/full stowed comparison", label=label, error=repr(exc))
            report["module_full_identity_mm3"] = identity

        # Explicit panel identity and all-component pose identity to saved A2.
        panel_identity = {}
        for state in FULL_STATES:
            p3, p2 = a3.get(state, {}), a2.get(state, {})
            for label in PANELS:
                if label not in p3 or label not in p2:
                    fail("panel missing for A2 identity", state=state, label=label)
                    continue
                delta = symmetric_difference_volume(p3[label], p2[label].translate((0, 0, -DROP_MM)))
                panel_identity[state + ":" + label] = delta
                if delta > BODY_TOL_MM3:
                    fail("panel/hinge geometry differs from A2 identity", state=state, label=label, difference_mm3=delta)
        report["panel_geometry_identity"] = panel_identity

        # Stowed dimensions, radius and measured body/housing floor contact.
        if BODY in full and HOUSING in full:
            body_b = bounds(full[BODY])
            housing_b = bounds(full[HOUSING])
            floor_gap = float(full[BODY].distance_to(full[HOUSING]))
            floor_overlap = volume(full[BODY] & full[HOUSING]) if floor_gap < CONTACT_TOL_MM else 0.0
            report["contacts"]["body_housing_floor"] = {
                "body_bounds_mm": body_b,
                "housing_bounds_mm": housing_b,
                "housing_bottom_z_mm": housing_b["z"][0],
                "expected_floor_z_mm": 63.25,
                "gap_mm": floor_gap,
                "overlap_mm3": floor_overlap,
            }
            if abs(housing_b["z"][0] - 63.25) > CONTACT_TOL_MM or floor_gap > CONTACT_TOL_MM or floor_overlap > OVERLAP_TOL_MM3:
                fail("body/housing floor seat", bottom_z_mm=housing_b["z"][0], gap_mm=floor_gap, overlap_mm3=floor_overlap)

            support_results = []
            for label in SUPPORTS:
                if label not in full:
                    fail("support part missing", label=label)
                    continue
                gap = float(full[label].distance_to(full[HOUSING]))
                overlap = volume(full[label] & full[HOUSING]) if gap < CONTACT_TOL_MM else 0.0
                support_results.append({"part": label, "housing_gap_mm": gap, "housing_overlap_mm3": overlap})
                if gap > CONTACT_TOL_MM:
                    fail("fixed root/carriage not seated in housing", label=label, gap_mm=gap)
            report["contacts"]["root_and_carriage_seating"] = support_results

        panel_tops = {name: bounds(full[name])["z"][1] for name in PANELS if name in full}
        cap_tops = {name: bounds(full[name])["z"][1] for name in CAP_PARTS if name in full}
        radial = {}
        for name, part in full.items():
            b = part.bounding_box()
            radial[name] = math.hypot(max(abs(float(b.min.Y)), abs(float(b.max.Y))),
                                      max(abs(float(b.min.Z)), abs(float(b.max.Z))))
        max_radius = max(radial.values()) if radial else None
        report["stowed"] = {
            "panel_top_z_mm_by_label": panel_tops,
            "port_front_top_z_mm": panel_tops.get("port_front"),
            "cap_part_top_z_mm_by_label": cap_tops,
            "maximum_cap_top_z_mm": max(cap_tops.values()) if cap_tops else None,
            "radial_bound_mm_by_label": radial,
            "complete_radial_bound_mm": max_radius,
            "radial_limit_mm_exclusive": 125.0,
        }
        if "port_front" not in panel_tops or abs(panel_tops["port_front"] - 86.0) > 0.001:
            fail("upper port front panel datum", expected_z_mm=86.0, actual_z_mm=panel_tops.get("port_front"))
        if not cap_tops or abs(max(cap_tops.values()) - 86.75) > 0.001:
            fail("maximum hinge cap datum", expected_z_mm=86.75, actual_z_mm=max(cap_tops.values()) if cap_tops else None)
        if max_radius is None or max_radius >= 125.0:
            fail("complete stowed radial envelope", actual_mm=max_radius, limit_mm_exclusive=125.0)

        # Saved mid/deployed are compared to motion generated from the saved A3 stowed parts.
        canonical_panels = {
            label: canonical_a3_panel(full[label], label.split("_")[0], label.split("_")[1])
            for label in PANELS if label in full
        }
        if len(canonical_panels) == 4:
            zero_pose = moved_a3_stowed(full, 0.0, canonical_panels)
            zero_deltas = {}
            for label in sorted(set(full) & set(zero_pose)):
                delta = symmetric_difference_volume(full[label], zero_pose[label])
                zero_deltas[label] = delta
                if delta > BODY_TOL_MM3:
                    fail("motion sample zero differs from saved A3 stowed", label=label, difference_mm3=delta)
            report["saved_pose_identity"]["Stowed_motion_sample"] = {
                "fraction": 0.0,
                "part_symmetric_difference_mm3": zero_deltas,
                "maximum_difference_mm3": max(zero_deltas.values()) if zero_deltas else None,
            }
        for state, fraction in (("Midfold", 0.5), ("Deployed", 1.0)):
            saved = a3.get(state, {})
            expected = moved_a3_stowed(full, fraction, canonical_panels) if len(canonical_panels) == 4 else {}
            pose_deltas = {}
            if set(saved) != set(expected):
                fail("saved motion state labels differ", state=state,
                     missing=sorted(set(expected) - set(saved)), extra=sorted(set(saved) - set(expected)))
            for label in sorted(set(saved) & set(expected)):
                try:
                    delta = symmetric_difference_volume(saved[label], expected[label])
                    pose_deltas[label] = delta
                    if delta > BODY_TOL_MM3:
                        fail("saved pose is not rigid A3 stowed motion", state=state, label=label, difference_mm3=delta)
                except Exception as exc:
                    fail("saved pose identity measurement", state=state, label=label, error=repr(exc))
            report["saved_pose_identity"][state] = {
                "fraction": fraction,
                "part_symmetric_difference_mm3": pose_deltas,
                "maximum_difference_mm3": max(pose_deltas.values()) if pose_deltas else None,
            }

        # Sample every simultaneous pose from saved A3 stowed geometry.  Only
        # housing/fixed-root overlap is intentional; body/hardware is never exempt.
        intentional = {
            frozenset((HOUSING, "starboard_fixed_root")),
            frozenset((HOUSING, "port_fixed_root")),
        }
        sample_min_panel = {name: {"clearance_mm": float("inf"), "fraction": None, "other": None} for name in PANELS}
        max_overlap = {"volume_mm3": 0.0, "fraction": None, "a": None, "b": None}
        support_sample_gaps = {name: {"max_gap_mm": 0.0, "fraction": None} for name in SUPPORTS}
        for i in range(21):
            fraction = i / 20
            sample = moved_a3_stowed(full, fraction, canonical_panels) if len(canonical_panels) == 4 else {}
            sample_record = {"fraction": fraction, "pair_count": 0, "minimum_panel_clearance_mm": None,
                             "maximum_unexpected_overlap_mm3": 0.0, "support_gaps_mm": {}}
            for support in SUPPORTS:
                if support in sample and HOUSING in sample:
                    gap = float(sample[support].distance_to(sample[HOUSING]))
                    sample_record["support_gaps_mm"][support] = gap
                    if gap > support_sample_gaps[support]["max_gap_mm"]:
                        support_sample_gaps[support] = {"max_gap_mm": gap, "fraction": fraction}
                    if gap > CONTACT_TOL_MM:
                        fail("motion support seating", fraction=fraction, label=support, gap_mm=gap)
            local_panel_min = float("inf")
            for a, b in itertools.combinations(sorted(sample), 2):
                sample_record["pair_count"] += 1
                try:
                    gap = float(sample[a].distance_to(sample[b]))
                    if a in PANELS or b in PANELS:
                        local_panel_min = min(local_panel_min, gap)
                        panel = a if a in PANELS else b
                        other = b if panel == a else a
                        if gap < sample_min_panel[panel]["clearance_mm"]:
                            sample_min_panel[panel] = {"clearance_mm": gap, "fraction": fraction, "other": other}
                        if gap <= PANEL_CLEARANCE_MIN_MM:
                            fail("panel clearance", fraction=fraction, panel=panel, other=other, gap_mm=gap)
                    pair = frozenset((a, b))
                    if gap < CONTACT_TOL_MM and pair not in intentional:
                        overlap = volume(sample[a] & sample[b])
                        sample_record["maximum_unexpected_overlap_mm3"] = max(
                            sample_record["maximum_unexpected_overlap_mm3"], overlap
                        )
                        if overlap > max_overlap["volume_mm3"]:
                            max_overlap = {"volume_mm3": overlap, "fraction": fraction, "a": a, "b": b}
                        if overlap >= OVERLAP_TOL_MM3:
                            fail("unexpected simultaneous overlap", fraction=fraction, a=a, b=b, overlap_mm3=overlap)
                except Exception as exc:
                    fail("simultaneous pair collision check", fraction=fraction, a=a, b=b, error=repr(exc))
            sample_record["minimum_panel_clearance_mm"] = local_panel_min if local_panel_min != float("inf") else None
            report["motion_samples"].append(sample_record)

        report["motion_summary"] = {
            "sample_count": len(report["motion_samples"]),
            "fractions": [item["fraction"] for item in report["motion_samples"]],
            "all_pair_checks_per_sample": True,
            "panel_clearance_minimum_mm_by_panel": sample_min_panel,
            "maximum_unexpected_overlap": max_overlap,
            "maximum_support_gap_mm_by_part": support_sample_gaps,
            "body_hardware_pairs_exempted": False,
        }
    except Exception as exc:
        fail("checker aborted on unexpected exception", error=repr(exc), traceback=traceback.format_exc())

    report["passed"] = not failures
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed": report["passed"],
        "report": str(REPORT_PATH),
        "A3_saved_artifacts_checked": len(report["artifacts"]),
        "motion_samples": len(report.get("motion_samples", [])),
        "body_exact_cut_delta_mm3": report.get("body_cut_comparison", {}).get("saved_vs_exact_cut_expected_symmetric_difference_mm3"),
        "body_outside_cut_delta_mm3": report.get("body_cut_comparison", {}).get("outside_cut_symmetric_difference_mm3"),
        "roof_top_z_mm": report.get("body_cut_comparison", {}).get("body_remaining_roof_top_z_mm"),
        "port_front_top_z_mm": report.get("stowed", {}).get("port_front_top_z_mm"),
        "maximum_cap_top_z_mm": report.get("stowed", {}).get("maximum_cap_top_z_mm"),
        "minimum_panel_clearance_mm": report.get("motion_summary", {}).get("panel_clearance_minimum_mm_by_panel"),
        "maximum_unexpected_overlap": report.get("motion_summary", {}).get("maximum_unexpected_overlap"),
        "failure_count": len(failures),
        "failures": failures,
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
