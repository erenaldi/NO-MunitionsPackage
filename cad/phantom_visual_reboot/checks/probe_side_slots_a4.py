"""In-memory A4 feasibility probe for restoring the unused A3 side channels."""
import itertools
import json
import sys
import traceback
from pathlib import Path

import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import check_interleaved_a3 as a3check  # noqa: E402

BODY = a3check.BODY
A2_BODY_PATH = ROOT / "STEP/O_Interleaved_A2_Stowed.step"
A3_STOWED_PATH = ROOT / "STEP/O_Interleaved_A3_Stowed.step"
REPORT_PATH = ROOT / "reviews/side_slots_a4_probe.json"
BODY_TOL_MM3 = a3check.BODY_TOL_MM3
OVERLAP_TOL_MM3 = a3check.OVERLAP_TOL_MM3
PANEL_CLEARANCE_MIN_MM = a3check.PANEL_CLEARANCE_MIN_MM
CONTACT_TOL_MM = a3check.CONTACT_TOL_MM

WELL = (-450.3, 550.3, -74.3, 74.3, 63.25, 100.0)
SLOTS = {
    "starboard_rear": (-430.0, 530.0, 0.0, 100.0, 65.7, 70.3),
    "starboard_front": (-430.0, 530.0, 0.0, 100.0, 76.2, 80.8),
    "port_rear": (-430.0, 530.0, -100.0, 0.0, 71.2, 75.8),
    "port_front": (-430.0, 530.0, -100.0, 0.0, 81.7, 86.3),
}
RESTORATION_REGIONS = {
    "starboard_rear": (-430.0, 530.0, -100.0, 0.0, 65.7, 70.3),
    "starboard_front": (-430.0, 530.0, -100.0, 0.0, 76.2, 80.8),
    "port_rear": (-430.0, 530.0, 0.0, 100.0, 71.2, 75.8),
    "port_front": (-430.0, 530.0, 0.0, 100.0, 81.7, 86.3),
}
PANELS = a3check.PANELS
INTENTIONAL_NONBODY_OVERLAPS = {
    frozenset((a3check.HOUSING, "starboard_fixed_root")),
    frozenset((a3check.HOUSING, "port_fixed_root")),
}


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


def make_box(extents):
    x0, x1, y0, y1, z0, z1 = extents
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    )


def union(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result + shape
    return result.clean()


def symdiff_volume(a, b):
    return volume(a - b) + volume(b - a)


def import_parts(path):
    parts, duplicates = a3check.parts_from_step(path)
    if duplicates:
        raise ValueError(f"duplicate STEP labels in {path}: {duplicates}")
    return parts


def run_probe():
    report = {
        "gate": "A4 unused side-slot restoration feasibility only",
        "scope": "In-memory candidate body; saved A3 nonbody geometry and motion helpers; no production build or output STEP.",
        "inputs": {
            "A2_original_body": str(A2_BODY_PATH),
            "A3_saved_stowed_assembly": str(A3_STOWED_PATH),
            "A3_motion_helper": str(ROOT / "src/check_interleaved_a3.py"),
        },
        "thresholds": {
            "body_difference_tolerance_mm3": BODY_TOL_MM3,
            "panel_clearance_strictly_greater_than_mm": PANEL_CLEARANCE_MIN_MM,
            "all_pair_overlap_strictly_less_than_mm3": OVERLAP_TOL_MM3,
            "contact_distance_mm": CONTACT_TOL_MM,
            "body_pair_exemptions": False,
            "documented_nonbody_overlap_exemptions": [
                [a3check.HOUSING, "starboard_fixed_root"],
                [a3check.HOUSING, "port_fixed_root"],
            ],
        },
        "candidate_cutters_mm": {
            "central_well": list(WELL),
            "side_slots": {label: list(extents) for label, extents in SLOTS.items()},
        },
        "restoration_regions_mm": {label: list(extents) for label, extents in RESTORATION_REGIONS.items()},
        "restored_volume_by_unused_slot_mm3": {},
        "body_checks": {},
        "nonbody_saved_a3_identity": {},
        "motion_samples": [],
        "motion_summary": {},
        "failures": [],
    }
    failures = report["failures"]

    def fail(check, **details):
        failures.append({"check": check, **details})

    try:
        a2_parts = import_parts(A2_BODY_PATH)
        a3_parts = import_parts(A3_STOWED_PATH)
        if BODY not in a2_parts or BODY not in a3_parts:
            raise KeyError(f"body label {BODY!r} not found in both saved STEP inputs")
        original = a2_parts[BODY]
        saved_a3_body = a3_parts[BODY]
        cutters = union([make_box(WELL)] + [make_box(box) for box in SLOTS.values()])
        candidate = (original - cutters).clean()
        candidate.label = BODY

        report["body_checks"]["original_a2_valid_single_solid"] = a3check.solid_valid(original)
        report["body_checks"]["candidate_valid_single_solid"] = a3check.solid_valid(candidate)
        report["body_checks"]["candidate_solid_count"] = len(candidate.solids())
        report["body_checks"]["candidate_volume_mm3"] = volume(candidate)
        if not a3check.solid_valid(candidate):
            fail("candidate body is not one valid positive solid",
                 solid_count=len(candidate.solids()), volume_mm3=volume(candidate))

        restored = (candidate - saved_a3_body).clean()
        unexpected_removed = (saved_a3_body - candidate).clean()
        allowed_regions = union([make_box(box) for box in RESTORATION_REGIONS.values()])
        changes = union([restored, unexpected_removed])
        outside_allowed = (changes - allowed_regions).clean()
        added_outside_a2 = (restored - original).clean()
        report["body_checks"].update({
            "restored_added_volume_mm3": volume(restored),
            "unexpected_removal_vs_saved_a3_mm3": volume(unexpected_removed),
            "restoration_outside_original_a2_mm3": volume(added_outside_a2),
            "material_change_outside_four_opposite_side_slots_mm3": volume(outside_allowed),
            "candidate_vs_a3_symmetric_difference_mm3": symdiff_volume(candidate, saved_a3_body),
        })
        if volume(added_outside_a2) > BODY_TOL_MM3:
            fail("restored material is not a subset of original A2 body",
                 volume_outside_a2_mm3=volume(added_outside_a2))
        if volume(outside_allowed) > BODY_TOL_MM3:
            fail("material changed outside the four unused opposite-side slots",
                 volume_outside_allowed_regions_mm3=volume(outside_allowed))
        if volume(unexpected_removed) > BODY_TOL_MM3:
            fail("candidate removed additional material relative to saved A3 body",
                 unexpected_removed_mm3=volume(unexpected_removed))

        for label, extents in RESTORATION_REGIONS.items():
            local_restoration = volume(restored & make_box(extents))
            report["restored_volume_by_unused_slot_mm3"][label] = local_restoration
            if local_restoration <= 0.0:
                fail("unused side slot has no restored body material",
                     slot=label, restored_volume_mm3=local_restoration)

        body_bounds = a3check.bounds(candidate)
        report["body_checks"]["candidate_bounds_mm"] = body_bounds
        report["body_checks"]["roof_top_z_mm"] = body_bounds["z"][1]

        # Keep the eleven nonbody parts sourced directly from saved A3. The
        # checker helper reconstructs the exact 21 established simultaneous poses.
        base = dict(a3_parts)
        base[BODY] = candidate
        canonical_panels = {
            label: a3check.canonical_a3_panel(
                a3_parts[label], label.split("_")[0], label.split("_")[1]
            )
            for label in PANELS
        }
        sample_zero = a3check.moved_a3_stowed(base, 0.0, canonical_panels)
        nonbody_deltas = {}
        for label in sorted(set(a3_parts) - {BODY}):
            delta = symdiff_volume(sample_zero[label], a3_parts[label])
            nonbody_deltas[label] = delta
            if delta > BODY_TOL_MM3:
                fail("saved A3 nonbody geometry changed at zero-pose reconstruction",
                     label=label, difference_mm3=delta)
        report["nonbody_saved_a3_identity"] = {
            "part_count": len(nonbody_deltas),
            "part_symmetric_difference_mm3": nonbody_deltas,
            "maximum_difference_mm3": max(nonbody_deltas.values()) if nonbody_deltas else None,
        }
        if len(nonbody_deltas) != 11:
            fail("saved A3 nonbody part count is not eleven", actual=len(nonbody_deltas))

        min_panel = {name: {"gap_mm": float("inf"), "fraction": None, "other": None}
                     for name in PANELS}
        min_all_pair = {"gap_mm": float("inf"), "fraction": None, "a": None, "b": None}
        max_overlap = {"volume_mm3": 0.0, "fraction": None, "a": None, "b": None}
        max_support_gap = {name: {"gap_mm": 0.0, "fraction": None}
                           for name in a3check.SUPPORTS}
        for i in range(21):
            fraction = i / 20
            sample = a3check.moved_a3_stowed(base, fraction, canonical_panels)
            local_panel_min = {"gap_mm": float("inf"), "pair": None}
            local_all_pair_min = {"gap_mm": float("inf"), "pair": None}
            sample_record = {"fraction": fraction, "part_count": len(sample),
                             "pair_count": 0, "minimum_panel_clearance": None,
                             "minimum_all_pair_gap": None,
                             "maximum_overlap_mm3": 0.0,
                             "support_gaps_mm": {}}

            for support in a3check.SUPPORTS:
                if support in sample and a3check.HOUSING in sample:
                    gap = float(sample[support].distance_to(sample[a3check.HOUSING]))
                    sample_record["support_gaps_mm"][support] = gap
                    if gap > max_support_gap[support]["gap_mm"]:
                        max_support_gap[support] = {"gap_mm": gap, "fraction": fraction}
                    if gap > CONTACT_TOL_MM:
                        fail("support no longer seated against housing",
                             fraction=fraction, pair=[support, a3check.HOUSING], gap_mm=gap)

            for a, b in itertools.combinations(sorted(sample), 2):
                sample_record["pair_count"] += 1
                try:
                    gap = float(sample[a].distance_to(sample[b]))
                    if gap < local_all_pair_min["gap_mm"]:
                        local_all_pair_min = {"gap_mm": gap, "pair": [a, b]}
                    if gap < min_all_pair["gap_mm"]:
                        min_all_pair = {"gap_mm": gap, "fraction": fraction, "a": a, "b": b}
                    if a in PANELS or b in PANELS:
                        panel = a if a in PANELS else b
                        other = b if panel == a else a
                        if gap < local_panel_min["gap_mm"]:
                            local_panel_min = {"gap_mm": gap, "pair": [panel, other]}
                        if gap < min_panel[panel]["gap_mm"]:
                            min_panel[panel] = {"gap_mm": gap, "fraction": fraction, "other": other}
                        if gap <= PANEL_CLEARANCE_MIN_MM:
                            fail("panel clearance not strictly above threshold",
                                 fraction=fraction, pair=[panel, other], gap_mm=gap)

                    # No pair exemptions: the body and every item of hardware
                    # participate in the same overlap-volume limit.
                    pair = frozenset((a, b))
                    if gap < CONTACT_TOL_MM and pair not in INTENTIONAL_NONBODY_OVERLAPS:
                        overlap = volume(sample[a] & sample[b])
                        sample_record["maximum_overlap_mm3"] = max(
                            sample_record["maximum_overlap_mm3"], overlap
                        )
                        if overlap > max_overlap["volume_mm3"]:
                            max_overlap = {"volume_mm3": overlap, "fraction": fraction,
                                           "a": a, "b": b}
                        if overlap >= OVERLAP_TOL_MM3:
                            fail("all-pair overlap reaches or exceeds threshold",
                                 fraction=fraction, pair=[a, b], overlap_mm3=overlap)
                except Exception as exc:
                    fail("motion pair geometry check failed", fraction=fraction,
                         pair=[a, b], error=repr(exc))

            sample_record["minimum_panel_clearance"] = local_panel_min
            sample_record["minimum_all_pair_gap"] = {
                "gap_mm": local_all_pair_min["gap_mm"],
                "fraction": fraction,
                "pair": local_all_pair_min["pair"],
            }
            report["motion_samples"].append(sample_record)

        # Retained A3 floor seat: the changed feature is above the well floor.
        if a3check.HOUSING in base:
            floor_gap = float(candidate.distance_to(base[a3check.HOUSING]))
            housing_bottom = a3check.bounds(base[a3check.HOUSING])["z"][0]
            floor_overlap = volume(candidate & base[a3check.HOUSING]) if floor_gap < CONTACT_TOL_MM else 0.0
            report["body_checks"]["housing_floor_seat"] = {
                "housing_bottom_z_mm": housing_bottom,
                "expected_bottom_z_mm": 63.25,
                "body_housing_gap_mm": floor_gap,
                "body_housing_overlap_mm3": floor_overlap,
            }
            if (abs(housing_bottom - 63.25) > CONTACT_TOL_MM
                    or floor_gap > CONTACT_TOL_MM
                    or floor_overlap >= OVERLAP_TOL_MM3):
                fail("body/housing floor seat not retained", housing_bottom_z_mm=housing_bottom,
                     gap_mm=floor_gap, overlap_mm3=floor_overlap)
        else:
            fail("housing missing; floor seat unavailable")

        report["motion_summary"] = {
            "sample_count": len(report["motion_samples"]),
            "fractions": [i / 20 for i in range(21)],
            "all_12_parts_pair_checked_each_sample": True,
            "pair_checks_per_sample": (len(base) * (len(base) - 1)) // 2,
            "minimum_panel_clearance_mm": min_panel,
            "minimum_all_pair_gap": min_all_pair,
            "maximum_all_pair_overlap_mm3": max_overlap,
            "maximum_support_gaps_mm": max_support_gap,
            "body_pair_exemptions": False,
            "documented_nonbody_overlap_exemptions": [
                [a3check.HOUSING, "starboard_fixed_root"],
                [a3check.HOUSING, "port_fixed_root"],
            ],
        }
    except Exception as exc:
        fail("probe aborted", error=repr(exc), traceback=traceback.format_exc())

    report["passed"] = not failures
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed": report["passed"],
        "report": str(REPORT_PATH),
        "candidate_body": report["body_checks"],
        "restored_volume_by_unused_slot_mm3": report["restored_volume_by_unused_slot_mm3"],
        "motion_summary": report["motion_summary"],
        "failure_count": len(failures),
        "failures": failures,
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run_probe())
