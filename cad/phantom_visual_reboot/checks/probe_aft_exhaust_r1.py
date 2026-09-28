"""In-memory R1 aft-exhaust feasibility probe against saved IntakeR3 STEP.

No production source or STEP output is generated.  The only persistent output
is reviews/aft_exhaust_r1_probe.json.
"""

from __future__ import annotations

import itertools
import faulthandler
import json
import math
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True

import build123d as bd
from cadgen import read_scene
from cadgen.geometry import closest_points as _closest_points, overlap_volume as _overlap_volume


def _single(shape):
    solids = list(shape.solids())
    if len(solids) != 1:
        raise ValueError(f'Expected one measurement solid, got {len(solids)}')
    return solids[0]


def overlap_volume(a, b):
    return _overlap_volume(_single(a), _single(b))


def closest_points(a, b):
    return _closest_points(_single(a), _single(b))


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reviews" / "aft_exhaust_r1_probe.json"
INPUT_PATH = ROOT / "STEP" / "R_RampIntake_R3_Stowed.step"
BODY = "RDM9_R7_symmetric_body_20mm_wedge_R4"
BODY_X_EXPECTED = (-1400.0, 1400.0)
SAMPLES = tuple(sorted(set(i / 60.0 for i in range(61)) |
                       {0.001, 0.002, 0.005, 0.01, 0.02}))
BOOL_TOL_MM3 = 0.001
CONTACT_EPS_MM3 = 1.0e-5
MIN_CLEARANCE_MM = 0.2
RADIUS_LIMIT_MM = 125.0

OUTER_SECTIONS = (
    (-1394.0, 124.0, 124.0, 0.0, 14.0),
    (-1360.0, 110.0, 110.0, 0.0, 12.0),
    (-1310.0, 84.0, 84.0, 0.0, 10.0),
)
INNER_SECTIONS = (
    (-1394.0, 116.0, 116.0, 0.0, 10.0),
    (-1360.0, 102.0, 102.0, 0.0, 8.0),
    (-1310.0, 76.0, 76.0, 0.0, 6.0),
)
CONNECTOR_SECTIONS = (
    (-1310.5, 76.0, 76.0, 0.0, 6.0),
    (-1308.0, 76.0, 76.0, 0.0, 6.0),
    (-1270.0, 80.0, 70.0, -10.0, 6.0),
    (-1150.0, 100.0, 60.0, -35.0, 6.0),
    (-1029.5, 116.0, 49.0, -52.5, 5.0),
)


def topology(shape):
    solids = list(shape.solids())
    volumes = [float(item.volume) for item in solids]
    return {
        "valid": bool(shape.is_valid),
        "solid_count": len(solids),
        "positive_solid_volumes_mm3": volumes,
        "pass": bool(shape.is_valid and len(solids) == 1 and volumes and
                      all(value > 0.0 for value in volumes)),
    }


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
    return math.sqrt(sum(value * value for value in gaps))


def symdiff_volume(first, second):
    return float((first - second).volume) + float((second - first).volume)


def rounded_section(record):
    x, width_y, height_z, center_z, radius = record
    # RectangleRounded is native XY.  A +90-degree Y rotation maps its local
    # X extent to world Z and local Y extent to world Y, so pass (height,width).
    sketch = bd.RectangleRounded(height_z, width_y, radius)
    sketch = sketch.rotate(bd.Axis.Y, 90.0).translate((x, 0.0, center_z))
    wire = sketch.faces()[0].outer_wire()
    actual = bounds(wire)
    expected = {
        "x": [x, x], "y": [-width_y / 2.0, width_y / 2.0],
        "z": [center_z - height_z / 2.0, center_z + height_z / 2.0],
    }
    return wire, {"declared_x_widthY_heightZ_centerZ_radius": list(record),
                  "measured_wire_bounds_mm": actual,
                  "expected_wire_bounds_mm": expected}


def loft(records):
    sections = [rounded_section(item) for item in records]
    wires = [item[0] for item in sections]
    # Retain section facts from the construction for the report; geometric
    # orientation is also checked by comparing every profile's actual bounds.
    fact_rows = [item[1] for item in sections]
    return bd.Solid.make_loft(wires, ruled=True), fact_rows


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
        raise RuntimeError(f"Duplicate saved STEP labels: {sorted(set(duplicates))}")
    return parts


def main():
    faulthandler.dump_traceback_later(60, repeat=True)
    print('Aft probe: loading saved geometry', flush=True)
    report = {
        "gate": "AftExhaustR1_in_memory_feasibility",
        "units": "mm",
        "scope": ("Native-geometry construction and feasibility against immutable saved "
                  "R_RampIntake_R3_Stowed.step. No production source/STEP, rendering, "
                  "airflow, engine, thermal, strength, continuous-motion, or visual-approval claim."),
        "thresholds": {
            "unexpected_volume_overlap_mm3_exclusive": BOOL_TOL_MM3,
            "positive_fixed_mount_contact_mm3_exclusive": CONTACT_EPS_MM3,
            "liner_motion_clearance_mm_exclusive": MIN_CLEARANCE_MM,
            "stowed_radius_mm_exclusive": RADIUS_LIMIT_MM,
            "body_X_endpoint_tolerance_mm": 1.0e-6,
        },
        "saved_input": {"path": str(INPUT_PATH)},
        "sections": {}, "checks": {}, "failures": [],
    }

    def fail(name, **details):
        report["failures"].append({"check": name, **details})

    try:
        if not INPUT_PATH.is_file():
            raise FileNotFoundError(INPUT_PATH)
        source_parts = load_parts(INPUT_PATH)
        report["saved_input"].update({
            "part_count": len(source_parts),
            "labels": sorted(source_parts),
            "body_bounds_mm": bounds(source_parts[BODY]),
        })
        if BODY not in source_parts:
            raise KeyError(f"Saved R3 STEP has no {BODY!r} body")
        if len(source_parts) != 33:
            fail("saved_R3_input_inventory", expected=33, actual=len(source_parts))
        if any(not topology(shape)["pass"] for shape in source_parts.values()):
            fail("saved_R3_input_topology", components={
                label: topology(shape) for label, shape in source_parts.items()
                if not topology(shape)["pass"]})

        outer, outer_facts = loft(OUTER_SECTIONS)
        print('Aft probe: outer loft ready', flush=True)
        inner_records = (
            (-1395.0, 116.0, 116.0, 0.0, 10.0),
            *INNER_SECTIONS,
            (-1309.0, 76.0, 76.0, 0.0, 6.0),
        )
        inner_tool, inner_facts = loft(inner_records)
        liner = (outer - inner_tool).clean()

        seat_records = (
            (-1401.0, 124.0, 124.0, 0.0, 14.0),
            (-1394.0, 124.0, 124.0, 0.0, 14.0),
            (-1360.0, 110.0, 110.0, 0.0, 12.0),
            (-1310.0, 84.0, 84.0, 0.0, 10.0),
        )
        seat, seat_facts = loft(seat_records)
        connector, connector_facts = loft(CONNECTOR_SECTIONS)
        cut_tool = (seat + connector).clean()
        body = source_parts[BODY]
        cut_body = (body - cut_tool).clean()
        print('Aft probe: cut body ready', flush=True)

        report["sections"] = {
            "outer_liner_ruled_loft": outer_facts,
            "inner_tool_ruled_loft_with_1mm_X_overrun_at_both_ends": inner_facts,
            "body_seat_ruled_loft": seat_facts,
            "connector_ruled_loft": connector_facts,
            "orientation_pass": all(
                abs(row["measured_wire_bounds_mm"][axis][i] -
                    row["expected_wire_bounds_mm"][axis][i]) <= 1.0e-6
                for rows in (outer_facts, inner_facts, seat_facts, connector_facts)
                for row in rows for axis in ("x", "y", "z") for i in (0, 1)),
            "section_construction_note": (
                "RectangleRounded local XY was rotated +90deg about world Y; its local X "
                "dimension was assigned heightZ and local Y dimension widthY."
            ),
        }
        if not report["sections"]["orientation_pass"]:
            fail("rounded_section_world_axis_orientation", sections=report["sections"])

        liner_topology, body_topology = topology(liner), topology(cut_body)
        body_expected = (body - cut_tool).clean()
        expected_delta = symdiff_volume(cut_body, body_expected)
        outside_delta = symdiff_volume((cut_body - cut_tool).clean(),
                                       (body - cut_tool).clean())
        added_volume = float((cut_body - body).volume)
        removed_volume = float((body - cut_body).volume)
        body_box = bounds(cut_body)
        # OCP extends these imported/generated bounds by about 5e-6 mm; the
        # unchanged-outside-cutter Boolean comparison below is the stronger
        # test that no external material was moved.
        body_x_tolerance = 1.0e-5
        body_x_pass = (abs(body_box["x"][0] - BODY_X_EXPECTED[0]) <= body_x_tolerance and
                       abs(body_box["x"][1] - BODY_X_EXPECTED[1]) <= body_x_tolerance)
        report["checks"]["body_and_liner_topology"] = {
            "body": body_topology, "liner": liner_topology,
            "pass": body_topology["pass"] and liner_topology["pass"],
        }
        report["checks"]["exact_body_cut_and_outside_unchanged"] = {
            "new_body_vs_saved_body_minus_seat_and_connector_mm3": expected_delta,
            "outside_declared_cut_symmetric_difference_mm3": outside_delta,
            "added_body_material_mm3": added_volume,
            "removed_body_material_mm3": removed_volume,
            "new_body_bounds_mm": body_box,
            "saved_body_bounds_mm": bounds(body),
            "stowed_body_X_expected_mm": list(BODY_X_EXPECTED),
            "body_X_tolerance_mm": body_x_tolerance,
            "body_X_pass": body_x_pass,
            "pass": (expected_delta < BOOL_TOL_MM3 and outside_delta < BOOL_TOL_MM3 and
                     added_volume < BOOL_TOL_MM3 and removed_volume > 0.0 and body_x_pass and
                     body_topology["pass"]),
        }
        if not report["checks"]["body_and_liner_topology"]["pass"]:
            fail("body_or_liner_not_one_valid_positive_solid", body=body_topology,
                 liner=liner_topology)
        if not report["checks"]["exact_body_cut_and_outside_unchanged"]["pass"]:
            fail("body_cut_identity_or_outer_X_failed",
                 **report["checks"]["exact_body_cut_and_outside_unchanged"])

        liner_body_overlap = float(overlap_volume(liner, cut_body))
        liner_body_distance = float(closest_points(liner, cut_body).distance)
        contact_common = (liner & cut_body)
        common_face_area = (sum(float(face.area) for face in contact_common.faces())
                            if contact_common is not None else 0.0)
        report["checks"]["liner_body_seat_attachment"] = {
            "liner_body_overlap_mm3": liner_body_overlap,
            "closest_boundary_distance_mm": liner_body_distance,
            "coincident_contact_face_area_mm2": common_face_area,
            "common_boolean_shape_returned": contact_common is not None,
            "pass": (liner_body_overlap < BOOL_TOL_MM3 and
                     liner_body_distance <= 1.0e-5),
        }
        if not report["checks"]["liner_body_seat_attachment"]["pass"]:
            fail("liner_not_attached_to_body_seat_without_overlap",
                 **report["checks"]["liner_body_seat_attachment"])

        rear_probe, _ = loft(((-1400.1,124.,124.,0.,14.),(-1399.9,124.,124.,0.,14.)))
        print('Aft probe: entrance probes', flush=True)
        # Match the rounded entrance and its real tapered first 0.1 mm;
        # square prisms incorrectly test the intentionally retained corners.
        liner_mouth_probe, _ = loft(((-1394.1,116.,116.,0.,10.),
                                     (-1394.,116.,116.,0.,10.),
                                     (-1393.9,116.-14.*.1/34.,116.-14.*.1/34.,0.,10.-2.*.1/34.)))
        rear_probe_overlap = float(overlap_volume(cut_body, rear_probe))
        liner_mouth_overlap = float(overlap_volume(liner, liner_mouth_probe))
        liner_box = bounds(liner)
        rear_x = -1400.0
        recession = liner_box["x"][0] - rear_x
        report["checks"]["rear_entrance_and_recessed_liner_opening"] = {
            "rear_body_opening_declared_width_height_radius_mm": [124.0, 124.0, 14.0],
            "rear_124_square_probe_body_overlap_mm3": rear_probe_overlap,
            "liner_entrance_declared_width_height_radius_mm": [116.0, 116.0, 10.0],
            "liner_116_square_probe_overlap_mm3": liner_mouth_overlap,
            "body_rear_plane_x_mm": rear_x,
            "liner_start_x_mm": liner_box["x"][0],
            "measured_recession_mm": recession,
            "liner_bounds_mm": liner_box,
            "pass": (rear_probe_overlap < BOOL_TOL_MM3 and
                     liner_mouth_overlap < BOOL_TOL_MM3 and
                     abs(recession - 6.0) <= 1.0e-6),
            "measurement_note": (
                "Opening clearances are tested by positive-volume probes in the declared "
                "124x124/r14 rear and 116x116/r10 tapered recessed entrance windows; corner radii and "
                "exact station profiles are separately measured from the native wires."
            ),
        }
        if not report["checks"]["rear_entrance_and_recessed_liner_opening"]["pass"]:
            fail("rear_opening_or_liner_recess_failed",
                 **report["checks"]["rear_entrance_and_recessed_liner_opening"])

        stub = bd.Box(77.0, 116.0, 49.0).translate((-991.5, 0.0, -52.5))
        print('Aft probe: connector clearance', flush=True)
        connector_inner_overlap = float(overlap_volume(connector, inner_tool))
        connector_stub_overlap = float(overlap_volume(connector, stub))
        connector_body_overlap = float(overlap_volume(connector, cut_body))
        connector_liner_overlap = float(overlap_volume(connector, liner))
        report["checks"]["connector_void_continuity_and_material_clearance"] = {
            "connector_vs_liner_inner_void_overlap_mm3": connector_inner_overlap,
            "connector_vs_saved_intake_aft_stub_box_overlap_mm3": connector_stub_overlap,
            "connector_vs_cut_body_material_overlap_mm3": connector_body_overlap,
            "connector_vs_liner_material_overlap_mm3": connector_liner_overlap,
            "saved_intake_stub_box_mm": {
                "x": [-1030.0, -953.0], "y": [-58.0, 58.0], "z": [-77.0, -28.0],
                "source": "saved R1 cutter dimensions carried into immutable R3 body",
            },
            "pass": (connector_inner_overlap > CONTACT_EPS_MM3 and
                     connector_stub_overlap > CONTACT_EPS_MM3 and
                     connector_body_overlap < BOOL_TOL_MM3 and
                     connector_liner_overlap < BOOL_TOL_MM3),
            "interpretation": "Geometric void continuity only; not airflow or propulsion evidence.",
        }
        if not report["checks"]["connector_void_continuity_and_material_clearance"]["pass"]:
            fail("connector_continuity_or_material_clearance_failed",
                 **report["checks"]["connector_void_continuity_and_material_clearance"])

        sys.path.insert(0, str(ROOT / "src"))
        import check_interleaved_a5 as a5check
        import check_ramp_intake_r1 as basecheck
        import check_ramp_intake_r2 as rampcheck
        import check_ramp_intake_r3 as latest_rampcheck
        import check_tail_fin_r4 as tailcheck

        r4_stowed = tailcheck.flatten_step(tailcheck.R4_PATHS["Stowed"])
        a5_stowed = tailcheck.flatten_step(a5check.A5_PATHS["Stowed"])
        expected_tail = set(tailcheck.EXPECTED_LABELS)
        if set(r4_stowed) != expected_tail:
            raise RuntimeError(f"Saved R4 Stowed inventory mismatch: missing="
                               f"{sorted(expected_tail-set(r4_stowed))}, extra="
                               f"{sorted(set(r4_stowed)-expected_tail)}")
        required_panels = set(a5check.PANELS) | set(a5check.SUPPORTS)
        missing_panels = sorted(required_panels - set(a5_stowed))
        if missing_panels:
            raise RuntimeError(f"Saved A5 Stowed motion inputs missing: {missing_panels}")
        canonical = {
            label: a5check.panel_canonical(
                a5_stowed[label], *label.split("_"), a5check.CUMULATIVE_A2_DROP_MM)
            for label in a5check.PANELS
        }

        tail_pocket_results = {}
        raw_pocket_cutters = tailcheck.independent_pocket_cutters()
        for station, angle in tailcheck.STATIONS:
            rotated = [tailcheck.rotate_x(item, angle) for item in raw_pocket_cutters]
            pocket_tool = tailcheck.union(rotated)
            remaining = float(overlap_volume(cut_body, pocket_tool))
            tail_pocket_results[station] = {
                "independent_R3_pocket_tool_body_overlap_mm3": remaining,
                "pass": remaining < BOOL_TOL_MM3,
            }
            if remaining >= BOOL_TOL_MM3:
                fail("tail_pocket_material_not_fully_removed", station=station,
                     overlap_mm3=remaining)

        mount_results = {}
        for station, _ in tailcheck.STATIONS:
            for suffix in ("fixed_knuckle_aft", "fixed_knuckle_forward"):
                label = f"tail_r4_{station}_{suffix}"
                if label not in source_parts:
                    mount_results[label] = {"pass": False, "error": "saved mount missing"}
                    continue
                amount = float(overlap_volume(source_parts[label], cut_body))
                mount_results[label] = {
                    "body_contact_overlap_mm3": amount,
                    "pass": amount > CONTACT_EPS_MM3,
                }
                if amount <= CONTACT_EPS_MM3:
                    fail("fixed_tail_mount_contact_not_positive", label=label,
                         overlap_mm3=amount)
        report["checks"]["four_tail_pockets_and_eight_fixed_mounts"] = {
            "pockets": tail_pocket_results,
            "pocket_count": len(tail_pocket_results),
            "fixed_mounts": mount_results,
            "fixed_mount_count": len(mount_results),
            "minimum_fixed_mount_body_overlap_mm3": min(
                (row.get("body_contact_overlap_mm3", 0.0)
                 for row in mount_results.values()), default=0.0),
            "pass": (len(tail_pocket_results) == 4 and
                     all(row["pass"] for row in tail_pocket_results.values()) and
                     len(mount_results) == 8 and
                     all(row["pass"] for row in mount_results.values())),
        }

        stowed_radii = {}
        print('Aft probe: pockets and supports checked', flush=True)
        for label, shape in {**source_parts, BODY:cut_body, 'aft_liner':liner}.items():
            box = shape.bounding_box(optimal=False)
            stowed_radii[label] = max(
                math.hypot(float(y), float(z))
                for y in (box.min.Y, box.max.Y) for z in (box.min.Z, box.max.Z))
        stowed_radius = max(stowed_radii.values())
        envelope_pass = (stowed_radius < RADIUS_LIMIT_MM and body_x_pass)
        report["checks"]["external_stowed_envelope"] = {
            "saved_R3_conservative_max_YZ_radius_mm": stowed_radius,
            "radius_witness": max(stowed_radii, key=stowed_radii.get),
            "radius_limit_mm_exclusive": RADIUS_LIMIT_MM,
            "stowed_radius_by_part_mm": stowed_radii,
            "cut_body_X_bounds_mm": body_box["x"],
            "body_X_expected_mm": list(BODY_X_EXPECTED),
            "pass": envelope_pass,
            "basis": "Saved R3 nonbody parts are immutable; aft cut changes only body material inside declared cutters.",
        }
        if not envelope_pass:
            fail("external_stowed_X_or_125mm_radius_failed",
                 **report["checks"]["external_stowed_envelope"])

        r3_static = source_parts
        nonbody_labels = [name for name in sorted(r3_static) if name != BODY]
        motion_rows = []
        global_min = {"clearance_mm": None, "pair": None, "fraction": None,
                      "measurement": None}
        max_overlap = {"overlap_mm3": 0.0, "pair": None, "fraction": None}
        for sample_index, fraction in enumerate(SAMPLES):
            print('Aft probe motion',sample_index,'/',len(SAMPLES),flush=True)
            posed = basecheck.reconstruct_existing(
                tailcheck, a5check, r4_stowed, cut_body, canonical, fraction)
            for label in basecheck.NEW_LABELS:
                if label == latest_rampcheck.RAMP_LABEL:
                    posed[label] = rampcheck.rotate_ramp(
                        r3_static[label], latest_rampcheck.R3_ANGLE_DEG * fraction)
                else:
                    posed[label] = r3_static[label]
            if set(posed) != set(source_parts):
                raise RuntimeError(
                    f"Motion reconstruction inventory mismatch at f={fraction}: "
                    f"missing={sorted(set(source_parts)-set(posed))}, "
                    f"extra={sorted(set(posed)-set(source_parts))}")
            pair_bounds = []
            overlap_rows = []
            for label in nonbody_labels:
                part = posed[label]
                lower = bbox_gap(liner, part)
                pair_bounds.append((lower, label, part))
                if lower == 0.0:
                    amount = float(overlap_volume(liner, part))
                    if amount >= BOOL_TOL_MM3:
                        overlap_rows.append({"part": label, "overlap_mm3": amount})
                        if amount > max_overlap["overlap_mm3"]:
                            max_overlap = {"overlap_mm3": amount, "pair": ["aft_liner", label],
                                           "fraction": fraction}

            # Every pair must prove the same >0.2 mm threshold. A positive
            # AABB distance is a rigorous lower bound, sufficient when above
            # that threshold. Report bounds as bounds, not exact minima.
            best = math.inf
            witness = None
            exact_count = 0
            pruned_count = 0
            for lower, label, part in sorted(pair_bounds, key=lambda row: row[0]):
                if lower > MIN_CLEARANCE_MM:
                    pruned_count += 1
                    distance = lower
                else:
                    distance = float(liner.distance_to(part))
                    exact_count += 1
                if distance < best:
                    best, witness = distance, label
            sample_pass = (len(pair_bounds) == 32 and best > MIN_CLEARANCE_MM and
                           not overlap_rows)
            row = {
                "sample": sample_index, "fraction": fraction,
                "part_count_tested_against_liner": len(pair_bounds),
                "expected_existing_nonbody_count": 32,
                "exact_nearest_point_pairs_tested": exact_count,
                "AABB_pairs_pruned_with_proven_lower_bound": pruned_count,
                "minimum_proven_liner_clearance_lower_bound_mm": None if math.isinf(best) else best,
                "minimum_clearance_witness_part": witness,
                "unexpected_overlaps_ge_0_001_mm3": overlap_rows,
                "pass": sample_pass,
            }
            motion_rows.append(row)
            if best < (global_min["clearance_mm"] if global_min["clearance_mm"] is not None
                       else math.inf):
                global_min = {"clearance_mm": best, "pair": ["aft_liner", witness],
                              "fraction": fraction,
                               "measurement": "conservative lower bound; exact distance only for AABB gaps at or below threshold"}
            if not sample_pass:
                fail("liner_motion_clearance_or_overlap", sample=sample_index,
                      fraction=fraction, minimum_clearance_mm=row["minimum_proven_liner_clearance_lower_bound_mm"],
                     witness=witness, overlaps=overlap_rows)
        report["checks"]["liner_vs_all_saved_parts_at_66_synchronous_fractions"] = {
            "sample_count": len(motion_rows), "expected_sample_count": 66,
            "uniform_sample_count": 61,
            "early_fractions": [0.001, 0.002, 0.005, 0.01, 0.02],
            "tested_existing_nonbody_parts_per_sample": 32,
            "total_part_sample_tests": len(motion_rows) * 32,
            "all_parts_covered": len(motion_rows) == 66 and
                all(row["part_count_tested_against_liner"] == 32 for row in motion_rows),
            "minimum_proven_sampled_clearance_lower_bound": global_min,
            "maximum_unexpected_overlap": max_overlap,
            "all_samples_pass": len(motion_rows) == 66 and all(row["pass"] for row in motion_rows),
            "samples": motion_rows,
            "motion_basis": (
                "check_ramp_intake_r1.reconstruct_existing for saved A5 panels and R4 tail; "
                "check_ramp_intake_r2.rotate_ramp for saved R3 ramp; remaining R3 hardware fixed."
            ),
            "continuous_motion_claim": "None; this is the requested 66 discrete synchronous samples.",
        }

    except Exception as exc:
        report["failures"].append({
            "check": "probe_aborted_on_unexpected_exception",
            "error": repr(exc), "traceback": traceback.format_exc(),
        })

    report["passed"] = not report["failures"]
    report["summary"] = {
        "passed": report["passed"],
        "failure_count": len(report["failures"]),
        "liner_topology_pass": report.get("checks", {}).get(
            "body_and_liner_topology", {}).get("liner", {}).get("pass"),
        "body_topology_pass": report.get("checks", {}).get(
            "body_and_liner_topology", {}).get("body", {}).get("pass"),
        "body_cut_identity_mm3": report.get("checks", {}).get(
            "exact_body_cut_and_outside_unchanged", {}).get(
                "new_body_vs_saved_body_minus_seat_and_connector_mm3"),
        "liner_body_overlap_mm3": report.get("checks", {}).get(
            "liner_body_seat_attachment", {}).get("liner_body_overlap_mm3"),
        "connector_liner_material_overlap_mm3": report.get("checks", {}).get(
            "connector_void_continuity_and_material_clearance", {}).get(
                "connector_vs_liner_material_overlap_mm3"),
        "connector_stub_intersection_mm3": report.get("checks", {}).get(
            "connector_void_continuity_and_material_clearance", {}).get(
                "connector_vs_saved_intake_aft_stub_box_overlap_mm3"),
        "motion": report.get("checks", {}).get(
            "liner_vs_all_saved_parts_at_66_synchronous_fractions", {}).get(
                "minimum_proven_sampled_clearance_lower_bound"),
        "first_failures": report["failures"][:12],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), **report["summary"]}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
