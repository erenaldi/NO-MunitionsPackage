"""Saved-artifact validation for the A5 covered interleaved-wing gate.

All model geometry is imported from saved STEP artifacts.  The body cutters,
cover envelope, and continuous pin-only swept solids below are independently
restated from the approved A5 dimensions; this checker does not import or call
the A5 generator's cutter functions.
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

from interleaved_wing_a import LAYERS, pose as a_pose  # noqa: E402
from joined_wing_r1 import (  # noqa: E402
    FRONT_LENGTH,
    OPEN_SEPARATION,
    REAR_LENGTH,
    STOW_SEPARATION,
    pose as link_pose,
)

BODY = "RDM9_R7_symmetric_body_20mm_wedge_R4"
HOUSING = "supported_housing"
COVER_LABEL = "top_cover"
DROP_A5_MM = 5.5
CUMULATIVE_A2_DROP_MM = 28.25
BODY_TOL_MM3 = 0.01
OVERLAP_TOL_MM3 = 0.001
PANEL_CLEARANCE_MIN_MM = 0.2
CONTACT_TOL_MM = 0.001

# Independent final A5 extents (mm). The four side slots are the A4 channels
# translated by -5.5 mm in Z; the cover seat and cover are intentionally
# described separately.
WELL_MM = (-450.3, 550.3, -74.3, 74.3, 57.75, 84.0)
SLOTS_MM = (
    (-430.0, 530.0, 0.0, 100.0, 60.2, 64.8),
    (-430.0, 530.0, 0.0, 100.0, 70.7, 75.3),
    (-430.0, 530.0, -100.0, 0.0, 65.7, 70.3),
    (-430.0, 530.0, -100.0, 0.0, 76.2, 80.8),
)
COVER_SEAT_MM = (-455.0, 555.0, -76.0, 76.0, 84.0, 100.0)
COVER_MM = (-455.0, 555.0, -76.0, 76.0, 84.0, 86.0)
PIN_CLEARANCE_MM = 0.3
PIN_RADII_MM = {"shaft": 3.5, "cap": 7.0}
PIN_Z_MM = {
    "starboard": {"shaft": (60.25, 75.25), "cap": (75.25, 75.75)},
    "port": {"shaft": (65.75, 80.75), "cap": (80.75, 81.25)},
}

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
STATES = ("Stowed", "Midfold", "Deployed")
EARLY_FRACTIONS = (0.0001, 0.00025, 0.0005, 0.001, 0.002, 0.003, 0.005, 0.01, 0.02)
REGULAR_FRACTIONS = tuple(i / 20 for i in range(21))
CRITICAL_SEPARATION_MM = math.sqrt(FRONT_LENGTH**2 - REAR_LENGTH**2)
TURNING_FRACTION = (
    (CRITICAL_SEPARATION_MM - STOW_SEPARATION)
    / (OPEN_SEPARATION - STOW_SEPARATION)
)
MOTION_FRACTIONS = tuple(sorted(set(REGULAR_FRACTIONS + EARLY_FRACTIONS + (TURNING_FRACTION,))))

A5_PATHS = {
    state: ROOT / f"STEP/O_Interleaved_A5_{state}.step"
    for state in ("Stowed", "Module_Stowed", "Midfold", "Deployed", "Body_Pocket", "Cover")
}
A4_PATHS = {
    state: ROOT / f"STEP/O_Interleaved_A4_{state}.step"
    for state in ("Stowed", "Module_Stowed", "Midfold", "Deployed")
}
A2_STOWED_PATH = ROOT / "STEP/O_Interleaved_A2_Stowed.step"
REPORT_PATH = ROOT / "reviews/interleaved_a5_checks.json"


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


def symdiff_volume(a, b):
    return volume(a - b) + volume(b - a)


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


def bounds(shape):
    b = shape.bounding_box()
    return {
        "x": [float(b.min.X), float(b.max.X)],
        "y": [float(b.min.Y), float(b.max.Y)],
        "z": [float(b.min.Z), float(b.max.Z)],
    }


def solid_valid(shape):
    return bool(shape.is_valid and len(shape.solids()) == 1 and volume(shape) > 0.0)


def parts_from_step(path):
    imported = bd.import_step(path)
    children = list(imported.children) or [imported]
    parts = {}
    duplicates = []
    for child in children:
        label = str(child.label)
        if label in parts:
            duplicates.append(label)
        parts[label] = child
    return parts, duplicates


def panel_canonical(part, side, kind, cumulative_drop_mm):
    """Undo the saved A2-frame placement of a stowed A5/A4 panel."""
    part = part.translate((0, 0, cumulative_drop_mm))
    if side == "port":
        part = part.mirror(bd.Plane.XZ)
    p = a_pose(0.0, "starboard")
    x, y = p[kind]
    z = LAYERS[side][0 if kind == "rear" else 1]
    return part.translate((-x, -y, -z)).rotate(bd.Axis.Z, -link_pose(0.0)[kind + "_angle"])


def move_saved_stowed(base, fraction, canonical_panels, cumulative_drop_mm):
    """Reconstruct one pose from saved stowed parts and the approved A law."""
    result = dict(base)
    start = {side: a_pose(0.0, side) for side in ("starboard", "port")}
    end = {side: a_pose(fraction, side) for side in ("starboard", "port")}
    panel_pose = a_pose(fraction, "starboard")
    for side in ("starboard", "port"):
        for kind in ("front", "rear"):
            label = side + "_" + kind
            local = canonical_panels[label]
            # Panels use one positive-Y local construction and are reflected
            # across XZ only after placement; unlike pins/carriages, their
            # pre-reflection Y translation is therefore the starboard pose.
            p = panel_pose
            z = LAYERS[side][0 if kind == "rear" else 1] - cumulative_drop_mm
            panel = local.rotate(bd.Axis.Z, link_pose(fraction)[kind + "_angle"])
            panel = panel.translate((p[kind][0], p[kind][1], z))
            if side == "port":
                panel = panel.mirror(bd.Plane.XZ)
            result[label] = panel
        for kind, key in (("carriage", "rear"), ("join", "joint")):
            dx = end[side][key][0] - start[side][key][0]
            dy = end[side][key][1] - start[side][key][1]
            result[side + "_" + kind] = base[side + "_" + kind].translate((dx, dy, 0))
    return result


def angular_sweep(side):
    """Return analytic angular extrema and their exact circle-center points."""
    center = (500.0, 30.0 if side == "starboard" else -30.0)
    candidates = []
    for fraction in (0.0, TURNING_FRACTION, 1.0):
        joint = a_pose(fraction, side)["joint"]
        theta = math.degrees(math.atan2(joint[1] - center[1], joint[0] - center[0]))
        candidates.append((theta, (float(joint[0]), float(joint[1])), fraction))
    low = min(candidates, key=lambda item: item[0])
    high = max(candidates, key=lambda item: item[0])
    return center, low, high, candidates


def pin_sweep_solid(side, feature, inflated):
    """Independent continuous circular-arc sweep with round endpoint caps."""
    center, low, high, candidates = angular_sweep(side)
    nominal_radius = PIN_RADII_MM[feature]
    radius = nominal_radius + (PIN_CLEARANCE_MM if inflated else 0.0)
    zlo, zhi = PIN_Z_MM[side][feature]
    if inflated:
        zlo -= PIN_CLEARANCE_MM
        zhi += PIN_CLEARANCE_MM
    inner = FRONT_LENGTH - radius
    outer = FRONT_LENGTH + radius
    theta = math.radians(low[0])
    points = [
        (center[0] + inner * math.cos(theta), center[1] + inner * math.sin(theta), zlo),
        (center[0] + outer * math.cos(theta), center[1] + outer * math.sin(theta), zlo),
        (center[0] + outer * math.cos(theta), center[1] + outer * math.sin(theta), zhi),
        (center[0] + inner * math.cos(theta), center[1] + inner * math.sin(theta), zhi),
    ]
    profile = bd.Face(bd.Wire.make_polygon(points, close=True))
    sector = bd.revolve(
        profile,
        axis=bd.Axis((center[0], center[1], 0), (0, 0, 1)),
        revolution_arc=high[0] - low[0],
    )
    disks = []
    for endpoint in (low[1], high[1]):
        disks.append(
            bd.Cylinder(
                radius,
                zhi - zlo,
                align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
            ).translate((endpoint[0], endpoint[1], zlo))
        )
    return (sector + disks[0] + disks[1]).clean(), {
        "circle_center_xy_mm": list(center),
        "circle_radius_mm": FRONT_LENGTH,
        "angular_interval_deg": [low[0], high[0]],
        "endpoint_centers_xy_mm": [list(low[1]), list(high[1])],
        "critical_turning_fraction": TURNING_FRACTION,
        "nominal_radius_mm": nominal_radius,
        "tool_radius_mm": radius,
        "z_interval_mm": [zlo, zhi],
        "all_analytic_candidate_angles_deg": [item[0] for item in candidates],
    }


def run_checks():
    report = {
        "artifact_prefix": "O_Interleaved_A5",
        "scope": (
            "Six saved A5 STEP artifacts; exact independent A2-minus-well/shifted-slots/"
            "cover-seat/pin-sweep body identity; continuous pin-only nominal and 0.3 mm "
            "inflated sweep intersections; cover/body contacts; four-state A4 translation "
            "identity; saved Midfold/Deployed reconstruction; 21 regular plus nine early "
            "and analytic-turning-point all-part motion samples. This is saved geometry "
            "validation, not strength, actuation, lock, or rack validation."
        ),
        "previous_A4_gate_context": {
            "prior_full_sample_pass_scope": (
                "The previous A4 saved checker covered 21 simultaneous motion poses only; "
                "it explicitly did not establish continuous sweep clearance."
            ),
            "continuous_pin_sweep_added_here": True,
            "early_A4_collision_regression_evidence": "measured below from saved A4 stowed geometry",
        },
        "thresholds": {
            "body_identity_mm3_exclusive": BODY_TOL_MM3,
            "body_added_material_mm3_exclusive": BODY_TOL_MM3,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "pin_nominal_or_inflated_intersection_mm3_exclusive": OVERLAP_TOL_MM3,
            "panel_clearance_mm_exclusive": PANEL_CLEARANCE_MIN_MM,
            "contact_gap_mm_inclusive": CONTACT_TOL_MM,
            "nonbody_A4_translation_mm": [0.0, 0.0, -DROP_A5_MM],
            "cumulative_A2_panel_frame_restore_mm": [0.0, 0.0, CUMULATIVE_A2_DROP_MM],
            "stowed_radial_bound_mm_exclusive": 125.0,
        },
        "independent_dimensions_mm": {
            "well": list(WELL_MM),
            "shifted_slots": [list(item) for item in SLOTS_MM],
            "cover_seat": list(COVER_SEAT_MM),
            "cover": list(COVER_MM),
            "pin_nominal_radii": PIN_RADII_MM,
            "pin_z_intervals": {
                side: {feature: list(z) for feature, z in features.items()}
                for side, features in PIN_Z_MM.items()
            },
            "pin_clearance_mm_radial_and_axial": PIN_CLEARANCE_MM,
            "motion_fractions": list(MOTION_FRACTIONS),
        },
        "artifacts": {},
        "topology": {},
        "failures": [],
    }
    failures = report["failures"]

    def fail(check, **detail):
        failures.append({"check": check, **detail})

    a5 = {}
    a4 = {}
    for state, path in A5_PATHS.items():
        try:
            parts, duplicates = parts_from_step(path)
            a5[state] = parts
            expected_count = 12 if state == "Module_Stowed" else (1 if state in ("Body_Pocket", "Cover") else 13)
            report["artifacts"][state] = {
                "path": str(path),
                "part_count": len(parts),
                "expected_part_count": expected_count,
                "labels": sorted(parts),
                "duplicate_labels": duplicates,
            }
            if len(parts) != expected_count:
                fail("A5 saved artifact part count", state=state, expected=expected_count, actual=len(parts))
            if duplicates:
                fail("duplicate A5 saved labels", state=state, labels=duplicates)
        except Exception as exc:
            a5[state] = {}
            report["artifacts"][state] = {"path": str(path), "import_error": repr(exc)}
            fail("A5 STEP import", state=state, path=str(path), error=repr(exc))

    for state, path in A4_PATHS.items():
        try:
            a4[state], duplicates = parts_from_step(path)
            if duplicates:
                fail("duplicate A4 reference labels", state=state, labels=duplicates)
        except Exception as exc:
            a4[state] = {}
            fail("A4 reference STEP import", state=state, path=str(path), error=repr(exc))

    try:
        a2, duplicates = parts_from_step(A2_STOWED_PATH)
        if duplicates:
            fail("duplicate A2 source labels", labels=duplicates)
    except Exception as exc:
        a2 = {}
        fail("A2 stowed STEP import", path=str(A2_STOWED_PATH), error=repr(exc))

    # Every saved A5 artifact part must be exactly one valid positive solid.
    topology = {}
    for state, parts in a5.items():
        for label, part in parts.items():
            try:
                record = {
                    "valid_single_positive_solid": solid_valid(part),
                    "solid_count": len(part.solids()),
                    "volume_mm3": volume(part),
                }
                topology[state + ":" + label] = record
                if not record["valid_single_positive_solid"]:
                    fail("A5 saved part topology", state=state, label=label,
                         solid_count=record["solid_count"], volume_mm3=record["volume_mm3"])
            except Exception as exc:
                topology[state + ":" + label] = {"error": repr(exc)}
                fail("A5 saved part topology measurement", state=state, label=label, error=repr(exc))
    report["topology"] = topology

    full = a5.get("Stowed", {})
    module = a5.get("Module_Stowed", {})
    if BODY not in full:
        fail("A5 full stowed body label missing", label=BODY)
    if COVER_LABEL not in full or COVER_LABEL not in module:
        fail("A5 saved top_cover label missing", full_has_cover=COVER_LABEL in full,
             module_has_cover=COVER_LABEL in module)
    if set(module) != set(full) - {BODY}:
        fail("A5 module/full label mismatch", differing=sorted(set(module) ^ (set(full) - {BODY})))

    # A5 carries all eleven saved A4 components down an additional 5.5 mm.
    nonbody_translation = {}
    for state in ("Stowed", "Module_Stowed", "Midfold", "Deployed"):
        current = a5.get(state, {})
        reference = a4.get(state, {})
        expected_labels = (set(reference) - {BODY}) | {COVER_LABEL}
        actual_nonbody = set(current) - ({BODY} if state != "Module_Stowed" else set())
        if actual_nonbody != expected_labels:
            fail("A4/A5 saved labels differ", state=state,
                 missing=sorted(expected_labels - actual_nonbody),
                 extra=sorted(actual_nonbody - expected_labels))
        deltas = {}
        for label in sorted(set(reference) & set(current)):
            if label == BODY:
                continue
            try:
                moved = reference[label].translate((0, 0, -DROP_A5_MM))
                delta = symdiff_volume(current[label], moved)
                deltas[label] = delta
                if delta > BODY_TOL_MM3:
                    fail("A5 nonbody part differs from saved A4 translated -5.5 mm",
                         state=state, label=label, difference_mm3=delta)
            except Exception as exc:
                fail("A4/A5 nonbody translation comparison", state=state, label=label, error=repr(exc))
        report.setdefault("A4_to_A5_nonbody_identity", {})[state] = {
            "part_count_compared": len(deltas),
            "symmetric_difference_mm3_by_part": deltas,
            "maximum_difference_mm3": max(deltas.values()) if deltas else None,
        }

    if len(module) == 12 and len(full) == 13:
        module_deltas = {}
        for label in sorted(module):
            delta = symdiff_volume(module[label], full[label])
            module_deltas[label] = delta
            if delta > BODY_TOL_MM3:
                fail("A5 module/full geometry differs", label=label, difference_mm3=delta)
        report["module_full_identity_mm3"] = {
            "part_count": len(module_deltas),
            "maximum_difference_mm3": max(module_deltas.values()) if module_deltas else None,
            "symmetric_difference_mm3_by_part": module_deltas,
        }

    # Cover-only artifact, bounds, thickness, and isolated/full identity.
    cover = full.get(COVER_LABEL)
    cover_only = a5.get("Cover", {})
    isolated_cover = next(iter(cover_only.values())) if len(cover_only) == 1 else None
    if cover is not None:
        cover_bounds = bounds(cover)
        cover_metrics = {
            "bounds_mm": cover_bounds,
            "volume_mm3": volume(cover),
            "expected_bounds_mm": {
                "x": [COVER_MM[0], COVER_MM[1]],
                "y": [COVER_MM[2], COVER_MM[3]],
                "z": [COVER_MM[4], COVER_MM[5]],
            },
            "expected_volume_mm3": (COVER_MM[1] - COVER_MM[0]) * (COVER_MM[3] - COVER_MM[2]) * (COVER_MM[5] - COVER_MM[4]),
        }
        cover_box_delta = symdiff_volume(cover, make_box(COVER_MM))
        cover_metrics["saved_cover_vs_independent_box_symmetric_difference_mm3"] = cover_box_delta
        if any(abs(cover_bounds[axis][i] - cover_metrics["expected_bounds_mm"][axis][i]) > 0.001
               for axis in ("x", "y", "z") for i in (0, 1)):
            fail("A5 cover bounds differ from independent box", actual=cover_bounds,
                 expected=cover_metrics["expected_bounds_mm"])
        if cover_box_delta > BODY_TOL_MM3:
            fail("A5 saved cover differs from independent specified box", difference_mm3=cover_box_delta)
        if isolated_cover is None:
            fail("A5 isolated Cover artifact is not a single part", part_count=len(cover_only))
        else:
            delta = symdiff_volume(cover, isolated_cover)
            cover_metrics["cover_only_vs_full_stowed_mm3"] = delta
            if delta > BODY_TOL_MM3:
                fail("A5 Cover artifact differs from full stowed top_cover", difference_mm3=delta)
        report["cover"] = cover_metrics
    else:
        fail("A5 top_cover unavailable for cover validation")

    # Rebuild the expected A5 body from saved original A2 and independently
    # restated box and analytic pin-sweep tools, not generator cutter helpers.
    original_body = a2.get(BODY)
    saved_body = full.get(BODY)
    pocket_parts = a5.get("Body_Pocket", {})
    pocket = next(iter(pocket_parts.values())) if len(pocket_parts) == 1 else None
    body_report = {"source_A2_stowed_step": str(A2_STOWED_PATH)}
    sweep_metrics = {}
    raw_sweep_tools = {}
    if original_body is not None and saved_body is not None:
        try:
            fixed_cutters = [make_box(WELL_MM)] + [make_box(item) for item in SLOTS_MM]
            fixed_cutters.append(make_box(COVER_SEAT_MM))
            for side in ("starboard", "port"):
                for feature in ("shaft", "cap"):
                    nominal, nominal_info = pin_sweep_solid(side, feature, False)
                    inflated, inflated_info = pin_sweep_solid(side, feature, True)
                    raw_sweep_tools[(side, feature, "nominal")] = nominal
                    raw_sweep_tools[(side, feature, "inflated")]= inflated
                    sweep_metrics[side + "_" + feature] = {
                        "nominal_sweep": nominal_info,
                        "inflated_sweep": inflated_info,
                    }
            clipped_inflated = [
                (raw_sweep_tools[(side, feature, "inflated")] & original_body).clean()
                for side in ("starboard", "port")
                for feature in ("shaft", "cap")
            ]
            all_cutters = union(fixed_cutters + clipped_inflated)
            expected_body = (original_body - all_cutters).clean()
            expected_delta = symdiff_volume(saved_body, expected_body)
            outside_delta = symdiff_volume(saved_body - all_cutters, original_body - all_cutters)
            added_volume = volume(saved_body - original_body)
            removed_volume = volume(original_body - saved_body)
            expected_removed = volume(original_body & all_cutters)
            body_bounds = bounds(saved_body)
            body_report.update({
                "saved_body_valid_single_positive_solid": solid_valid(saved_body),
                "independent_expected_body_valid_single_positive_solid": solid_valid(expected_body),
                "saved_vs_exact_A2_minus_independent_cutters_symmetric_difference_mm3": expected_delta,
                "body_outside_cut_symmetric_difference_mm3": outside_delta,
                "original_A2_material_added_mm3": added_volume,
                "original_A2_material_removed_mm3": removed_volume,
                "expected_original_intersection_with_cutters_mm3": expected_removed,
                "removed_volume_error_mm3": abs(removed_volume - expected_removed),
                "saved_body_bounds_mm": body_bounds,
                "saved_body_roof_top_z_mm": body_bounds["z"][1],
                "body_pocket_vs_full_stowed_symmetric_difference_mm3": (
                    symdiff_volume(saved_body, pocket) if pocket is not None else None
                ),
            })
            if expected_delta > BODY_TOL_MM3:
                fail("saved A5 body differs from independent exact A2 cut", difference_mm3=expected_delta)
            if outside_delta > BODY_TOL_MM3:
                fail("A5 body changed outside independently specified cut union", difference_mm3=outside_delta)
            if added_volume > BODY_TOL_MM3:
                fail("A5 body adds material relative to original A2", added_mm3=added_volume)
            if abs(removed_volume - expected_removed) > BODY_TOL_MM3:
                fail("A5 removed volume differs from independent cutter intersection",
                     error_mm3=abs(removed_volume - expected_removed))
            if not solid_valid(expected_body):
                fail("independent expected A5 body topology invalid")
            if abs(body_bounds["z"][1] - 86.0) > 0.001:
                fail("A5 body roof top datum", expected_z_mm=86.0, actual_z_mm=body_bounds["z"][1])
            if pocket is None:
                fail("A5 Body_Pocket is not a single saved part", part_count=len(pocket_parts))
            elif body_report["body_pocket_vs_full_stowed_symmetric_difference_mm3"] > BODY_TOL_MM3:
                fail("A5 Body_Pocket differs from full stowed body",
                     difference_mm3=body_report["body_pocket_vs_full_stowed_symmetric_difference_mm3"])
        except Exception as exc:
            body_report["independent_body_comparison_error"] = repr(exc)
            fail("independent A5 body comparison failed", error=repr(exc), traceback=traceback.format_exc())
    else:
        fail("A5 independent body comparison unavailable", has_A2_body=original_body is not None,
             has_saved_body=saved_body is not None)
    body_report["independent_pin_sweep_definitions"] = sweep_metrics
    report["body_cut_comparison"] = body_report

    # Verify the nominal pin envelope AND the 0.3 mm radial/axial inflated tool
    # against saved body and cover; no other moving component is included here.
    pin_intersections = {}
    if saved_body is not None and cover is not None:
        for side in ("starboard", "port"):
            for feature in ("shaft", "cap"):
                row = {}
                for size in ("nominal", "inflated"):
                    tool = raw_sweep_tools.get((side, feature, size))
                    if tool is None:
                        continue
                    body_overlap = volume(tool & saved_body)
                    cover_overlap = volume(tool & cover)
                    row[size] = {
                        "saved_body_intersection_mm3": body_overlap,
                        "cover_intersection_mm3": cover_overlap,
                    }
                    if body_overlap >= OVERLAP_TOL_MM3:
                        fail("continuous pin sweep intersects saved body", side=side, feature=feature,
                             sweep=size, overlap_mm3=body_overlap)
                    if cover_overlap >= OVERLAP_TOL_MM3:
                        fail("continuous pin sweep intersects saved cover", side=side, feature=feature,
                             sweep=size, overlap_mm3=cover_overlap)
                pin_intersections[side + "_" + feature] = row
    else:
        fail("continuous pin sweep checks unavailable", has_body=saved_body is not None, has_cover=cover is not None)
    report["continuous_pin_only_sweep_intersections"] = pin_intersections

    # Cover underside/roof, the 2.75 mm internal pin gap, frame floor contact,
    # and a positive ledge-support area proxy from a 0.01 mm surface band.
    contact_report = {}
    if saved_body is not None and cover is not None:
        body_cover_gap = float(saved_body.distance_to(cover))
        body_cover_overlap = volume(saved_body & cover) if body_cover_gap <= CONTACT_TOL_MM else 0.0
        landing_band = make_box((COVER_MM[0], COVER_MM[1], COVER_MM[2], COVER_MM[3], 83.99, 84.0))
        landing_volume = volume(saved_body & landing_band)
        landing_area_proxy = landing_volume / 0.01
        join_tops = {side: bounds(full[side + "_join"])["z"][1]
                     for side in ("starboard", "port") if side + "_join" in full}
        highest_pin_top = max(join_tops.values()) if join_tops else None
        underside = bounds(cover)["z"][0]
        pin_gap = underside - highest_pin_top if highest_pin_top is not None else None
        contact_report["body_cover"] = {
            "gap_mm": body_cover_gap,
            "overlap_mm3": body_cover_overlap,
            "cover_underside_z_mm": underside,
            "cover_roof_z_mm": bounds(cover)["z"][1],
            "expected_underside_z_mm": 84.0,
            "expected_roof_z_mm": 86.0,
            "landing_band_z_mm": [83.99, 84.0],
            "landing_band_volume_mm3": landing_volume,
            "positive_ledge_support_area_proxy_mm2": landing_area_proxy,
        }
        contact_report["internal_join_pin_clearance"] = {
            "top_z_mm_by_side": join_tops,
            "highest_internal_pin_top_z_mm": highest_pin_top,
            "cover_underside_z_mm": underside,
            "gap_mm": pin_gap,
            "expected_gap_mm": 2.75,
        }
        if body_cover_gap > CONTACT_TOL_MM or body_cover_overlap >= OVERLAP_TOL_MM3:
            fail("A5 cover/body contact", gap_mm=body_cover_gap, overlap_mm3=body_cover_overlap)
        if landing_volume <= 0.0:
            fail("A5 cover ledge has no positive support area proxy", landing_band_volume_mm3=landing_volume)
        if abs(underside - 84.0) > 0.001 or abs(bounds(cover)["z"][1] - 86.0) > 0.001:
            fail("A5 cover roof/underside datum", underside_z_mm=underside, roof_z_mm=bounds(cover)["z"][1])
        if highest_pin_top is None or abs(highest_pin_top - 81.25) > 0.001 or abs(pin_gap - 2.75) > 0.001:
            fail("A5 internal pin-to-cover clearance datum", highest_pin_top_z_mm=highest_pin_top,
                 gap_mm=pin_gap, expected_highest_z_mm=81.25, expected_gap_mm=2.75)

    housing = full.get(HOUSING)
    if saved_body is not None and housing is not None:
        housing_bounds = bounds(housing)
        floor_gap = float(saved_body.distance_to(housing))
        floor_overlap = volume(saved_body & housing) if floor_gap <= CONTACT_TOL_MM else 0.0
        contact_report["body_housing_floor"] = {
            "housing_bottom_z_mm": housing_bounds["z"][0],
            "expected_floor_z_mm": 57.75,
            "gap_mm": floor_gap,
            "overlap_mm3": floor_overlap,
        }
        if abs(housing_bounds["z"][0] - 57.75) > CONTACT_TOL_MM or floor_gap > CONTACT_TOL_MM or floor_overlap >= OVERLAP_TOL_MM3:
            fail("A5 body/housing floor contact", housing_bottom_z_mm=housing_bounds["z"][0],
                 gap_mm=floor_gap, overlap_mm3=floor_overlap)
    else:
        fail("A5 body/housing floor contact unavailable", has_body=saved_body is not None, has_housing=housing is not None)
    report["contacts"] = contact_report

    # Complete stowed Y/Z radial envelope includes body, cover, and every part.
    stowed_radial = {}
    for label, part in full.items():
        b = bounds(part)
        stowed_radial[label] = math.hypot(max(abs(b["y"][0]), abs(b["y"][1])),
                                         max(abs(b["z"][0]), abs(b["z"][1])))
    max_radial = max(stowed_radial.values()) if stowed_radial else None
    report["stowed_complete_radial_envelope"] = {
        "radius_formula": "hypot(max(abs(Ybounds)), max(abs(Zbounds)))",
        "radius_mm_by_part": stowed_radial,
        "maximum_radius_mm": max_radial,
        "limit_mm_exclusive": 125.0,
    }
    if max_radial is None or max_radial >= 125.0:
        fail("A5 complete stowed radial envelope", actual_mm=max_radial, limit_mm=125.0)

    # Exact zero, saved Midfold, and Deployed reconstructed from saved Stowed.
    canonical_panels = {}
    if all(label in full for label in PANELS):
        canonical_panels = {
            label: panel_canonical(full[label], label.split("_")[0], label.split("_")[1], CUMULATIVE_A2_DROP_MM)
            for label in PANELS
        }
        pose_identity = {}
        for state, fraction in (("Stowed", 0.0), ("Midfold", 0.5), ("Deployed", 1.0)):
            expected = move_saved_stowed(full, fraction, canonical_panels, CUMULATIVE_A2_DROP_MM)
            saved = a5.get(state, {})
            deltas = {}
            if set(saved) != set(expected):
                fail("A5 saved pose labels differ from reconstructed motion", state=state,
                     missing=sorted(set(expected) - set(saved)), extra=sorted(set(saved) - set(expected)))
            for label in sorted(set(saved) & set(expected)):
                delta = symdiff_volume(saved[label], expected[label])
                deltas[label] = delta
                if delta > BODY_TOL_MM3:
                    fail("A5 saved pose differs from reconstructed stowed motion", state=state,
                         label=label, difference_mm3=delta)
            pose_identity[state] = {
                "fraction": fraction,
                "part_count_compared": len(deltas),
                "maximum_symmetric_difference_mm3": max(deltas.values()) if deltas else None,
                "symmetric_difference_mm3_by_part": deltas,
            }
        report["saved_pose_identity"] = pose_identity
    else:
        fail("A5 stowed panel canonicalization unavailable", missing=sorted(set(PANELS) - set(full)))

    # Regression baseline: re-run requested early fractions against the saved
    # A4 body and saved A4 stowed moving join parts. The prior 21-pose check is
    # not treated as evidence of continuous clearance.
    a4_early = {"fractions": list(MOTION_FRACTIONS), "join_body_collisions": [], "samples": []}
    a4_stowed = a4.get("Stowed", {})
    if BODY in a4_stowed and all(label in a4_stowed for label in PANELS):
        a4_canonical = {
            label: panel_canonical(a4_stowed[label], label.split("_")[0], label.split("_")[1], 22.75)
            for label in PANELS
        }
        for fraction in MOTION_FRACTIONS:
            moved = move_saved_stowed(a4_stowed, fraction, a4_canonical, 22.75)
            sample = {"fraction": fraction, "join_body": {}}
            for side in ("starboard", "port"):
                label = side + "_join"
                pin = moved.get(label)
                if pin is None:
                    continue
                gap = float(a4_stowed[BODY].distance_to(pin))
                overlap = volume(a4_stowed[BODY] & pin) if gap <= CONTACT_TOL_MM else 0.0
                sample["join_body"][side] = {"gap_mm": gap, "overlap_mm3": overlap}
                if overlap >= OVERLAP_TOL_MM3:
                    a4_early["join_body_collisions"].append({
                        "fraction": fraction, "side": side, "overlap_mm3": overlap,
                    })
            a4_early["samples"].append(sample)
        a4_early["collision_count"] = len(a4_early["join_body_collisions"])
        a4_early["early_collision_fractions"] = sorted({item["fraction"] for item in a4_early["join_body_collisions"]})
    else:
        fail("A4 early-collision regression baseline unavailable", has_body=BODY in a4_stowed,
             missing_panels=sorted(set(PANELS) - set(a4_stowed)))
    report["previous_A4_early_collision_regression"] = a4_early

    # Every saved-part pair through the required regular/early/critical poses.
    # Only the two housing/fixed-root pairs are intentional; no body/cover pair
    # is exempt, and cover/body contact is assessed above.
    intentional = {
        frozenset((HOUSING, "starboard_fixed_root")),
        frozenset((HOUSING, "port_fixed_root")),
    }
    min_panel = {label: {"clearance_mm": float("inf"), "fraction": None, "other": None} for label in PANELS}
    max_unexpected = {"overlap_mm3": 0.0, "fraction": None, "a": None, "b": None}
    motion_records = []
    if len(canonical_panels) == 4 and len(full) == 13:
        for fraction in MOTION_FRACTIONS:
            sample = move_saved_stowed(full, fraction, canonical_panels, CUMULATIVE_A2_DROP_MM)
            pair_count = 0
            local_panel_clearance = float("inf")
            local_collisions = []
            for a, b in itertools.combinations(sorted(sample), 2):
                pair_count += 1
                try:
                    gap = float(sample[a].distance_to(sample[b]))
                    if a in PANELS or b in PANELS:
                        panel = a if a in PANELS else b
                        other = b if panel == a else a
                        local_panel_clearance = min(local_panel_clearance, gap)
                        if gap < min_panel[panel]["clearance_mm"]:
                            min_panel[panel] = {"clearance_mm": gap, "fraction": fraction, "other": other}
                        if gap <= PANEL_CLEARANCE_MIN_MM:
                            fail("A5 motion panel clearance", fraction=fraction, panel=panel,
                                 other=other, gap_mm=gap)
                    pair = frozenset((a, b))
                    if gap <= CONTACT_TOL_MM and pair not in intentional:
                        overlap = volume(sample[a] & sample[b])
                        if overlap > max_unexpected["overlap_mm3"]:
                            max_unexpected = {"overlap_mm3": overlap, "fraction": fraction, "a": a, "b": b}
                        if overlap >= OVERLAP_TOL_MM3:
                            collision = {"a": a, "b": b, "overlap_mm3": overlap}
                            local_collisions.append(collision)
                            fail("A5 unexpected simultaneous part overlap", fraction=fraction, **collision)
                except Exception as exc:
                    fail("A5 simultaneous pair measurement", fraction=fraction, a=a, b=b, error=repr(exc))
            motion_records.append({
                "fraction": fraction,
                "pair_count": pair_count,
                "minimum_panel_clearance_mm": local_panel_clearance if local_panel_clearance != float("inf") else None,
                "unexpected_overlap_count": len(local_collisions),
                "maximum_unexpected_overlap_mm3": max((item["overlap_mm3"] for item in local_collisions), default=0.0),
                "unexpected_pairs": local_collisions,
            })
    else:
        fail("A5 full all-pair motion check unavailable", canonical_panel_count=len(canonical_panels),
             stowed_part_count=len(full))
    report["motion_summary"] = {
        "sample_count": len(motion_records),
        "regular_sample_count": len(REGULAR_FRACTIONS),
        "early_sample_count": len(EARLY_FRACTIONS),
        "analytic_turning_fraction": TURNING_FRACTION,
        "all_pair_checks_per_sample": True,
        "pair_count_per_sample": 78,
        "panel_clearance_minimum_mm_by_panel": min_panel,
        "maximum_unexpected_overlap": max_unexpected,
        "intentional_overlap_exemptions": [
            [HOUSING, "starboard_fixed_root"], [HOUSING, "port_fixed_root"],
        ],
        "body_or_cover_overlap_exemptions": False,
        "samples": motion_records,
    }

    # The joint center follows a 900 mm circle; explicitly record sampled
    # consistency in addition to the exact endpoint/interior-extremum bounds.
    circle_metrics = {}
    for side in ("starboard", "port"):
        center = (500.0, 30.0 if side == "starboard" else -30.0)
        radii = []
        angles = []
        for i in range(1001):
            joint = a_pose(i / 1000, side)["joint"]
            dx, dy = joint[0] - center[0], joint[1] - center[1]
            radii.append(math.hypot(dx, dy))
            angles.append(math.degrees(math.atan2(dy, dx)))
        _, low, high, candidates = angular_sweep(side)
        covered = min(angles) >= low[0] - 1e-9 and max(angles) <= high[0] + 1e-9
        circle_metrics[side] = {
            "center_xy_mm": list(center),
            "radius_target_mm": FRONT_LENGTH,
            "sampled_1001_max_radius_error_mm": max(abs(value - FRONT_LENGTH) for value in radii),
            "analytic_candidate_fractions": [item[2] for item in candidates],
            "analytic_extreme_angles_deg": [low[0], high[0]],
            "sampled_1001_angle_interval_deg": [min(angles), max(angles)],
            "analytic_interval_covers_sampled_angles": covered,
        }
        if max(abs(value - FRONT_LENGTH) for value in radii) > 1e-8 or not covered:
            fail("A5 analytic joint circle/extrema coverage", side=side,
                 max_radius_error_mm=max(abs(value - FRONT_LENGTH) for value in radii),
                 interval_covers_samples=covered)
    report["joint_circle_analytic_sweep"] = {
        "interior_turning_separation_mm": CRITICAL_SEPARATION_MM,
        "interior_turning_fraction": TURNING_FRACTION,
        "circle_radius_mm": FRONT_LENGTH,
        "circle_center_xy_mm_by_side": {side: [500.0, 30.0 if side == "starboard" else -30.0]
                                        for side in ("starboard", "port")},
        "analytic_sweep_by_side": circle_metrics,
    }

    report["passed"] = not failures
    return report


def main():
    try:
        report = run_checks()
    except Exception as exc:
        report = {
            "artifact_prefix": "O_Interleaved_A5",
            "passed": False,
            "failures": [{"check": "checker aborted on unexpected exception",
                          "error": repr(exc), "traceback": traceback.format_exc()}],
        }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    body = report.get("body_cut_comparison", {})
    motion = report.get("motion_summary", {})
    print(json.dumps({
        "passed": report.get("passed", False),
        "report": str(REPORT_PATH),
        "A5_saved_artifacts_checked": len(report.get("artifacts", {})),
        "part_counts": {state: info.get("part_count") for state, info in report.get("artifacts", {}).items()},
        "body_exact_cut_delta_mm3": body.get("saved_vs_exact_A2_minus_independent_cutters_symmetric_difference_mm3"),
        "body_outside_cut_delta_mm3": body.get("body_outside_cut_symmetric_difference_mm3"),
        "body_added_material_mm3": body.get("original_A2_material_added_mm3"),
        "pin_sweep_intersections": report.get("continuous_pin_only_sweep_intersections", {}),
        "body_cover_contact": report.get("contacts", {}).get("body_cover"),
        "body_housing_floor": report.get("contacts", {}).get("body_housing_floor"),
        "complete_stowed_radius_mm": report.get("stowed_complete_radial_envelope", {}).get("maximum_radius_mm"),
        "motion_samples": motion.get("sample_count"),
        "minimum_panel_clearance_mm": motion.get("panel_clearance_minimum_mm_by_panel"),
        "maximum_unexpected_overlap": motion.get("maximum_unexpected_overlap"),
        "A4_early_regression_collision_count": report.get("previous_A4_early_collision_regression", {}).get("collision_count"),
        "failure_count": len(report.get("failures", [])),
        "failures": report.get("failures", []),
    }, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
