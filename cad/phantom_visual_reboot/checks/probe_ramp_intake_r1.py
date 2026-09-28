"""In-memory feasibility probe for the R1 belly ramp intake trial geometry.

Reads the saved 29-part Tail R4 Stowed STEP and the approved A5 pose helper.
No model source, STEP, mesh, or render is written; only the review JSON is saved.
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
from cadgen.geometry import closest_points, overlap_volume


ROOT = Path(__file__).resolve().parents[1]
INPUT_STEP = ROOT / "STEP" / "Q_Tail_R4_Four_Stowed.step"
REPORT_PATH = ROOT / "reviews" / "ramp_intake_r1_probe.json"
sys.path.insert(0, str(ROOT / "src"))

import check_tail_fin_r4 as r4check  # noqa: E402
import check_interleaved_a5 as a5check  # noqa: E402


BODY = r4check.BODY
STATIONS = r4check.STATIONS
TAIL_SUFFIXES = r4check.TAIL_SUFFIXES
TAIL_LABELS = r4check.TAIL_LABELS
EXPECTED_LABELS = r4check.EXPECTED_LABELS
HINGE_X = -950.0
HINGE_Z = -83.0
ANGLE_DEG = 5.0
RAMP_ANGLE_DEG = ANGLE_DEG
FOLD_ANGLE_DEG = r4check.FOLD_ANGLE_DEG
FLOOR_X = (-950.0, -290.0)
FLOOR_Y = (-64.0, 64.0)
FLOOR_Z = (-86.0, -83.0)
CHEEK_THICKNESS = 2.0
BODY_BELLY_Z = -86.0
OVERLAP_TOL_MM3 = 0.001
MIN_CLEARANCE_MM = 0.2
CONTACT_EPS_MM3 = 1.0e-5
BOOL_TOL_MM3 = 0.01
EARLY_FRACTIONS = (0.001, 0.002, 0.005, 0.01, 0.02)
FRACTIONS = tuple(sorted(set(i / 60.0 for i in range(61)) | set(EARLY_FRACTIONS)))
MOUNT_BODY_PAIRS = {
    frozenset(("fixed_mount_negative_y", BODY)),
    frozenset(("fixed_mount_positive_y", BODY)),
}


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


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


def make_box(x0, x1, y0, y1, z0, z1):
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
    )


def cylinder_y(radius, y0, y1, x=HINGE_X, z=HINGE_Z):
    return bd.Cylinder(radius, y1 - y0).rotate(bd.Axis.X, 90.0).translate(
        (x, (y0 + y1) / 2.0, z)
    )


def union(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result + shape
    result = result.clean()
    solids = list(result.solids())
    return solids[0] if len(solids) == 1 else result


def one_solid(shape):
    solids = list(shape.solids())
    return {
        "valid": bool(shape.is_valid),
        "solid_count": len(solids),
        "solid_volumes_mm3": [float(solid.volume) for solid in solids],
        "volume_mm3": volume(shape),
        "pass": bool(shape.is_valid and len(solids) == 1 and volume(shape) > 0.0),
    }


def triangle_cheek(y0):
    top_z = -83.0 + 650.0 * math.tan(math.radians(ANGLE_DEG))
    wire = bd.Wire.make_polygon(
        [(-950.0, y0, -83.0), (-300.0, y0, -83.0), (-300.0, y0, top_z)],
        close=True,
    )
    return bd.extrude(bd.Face(wire), amount=CHEEK_THICKNESS, dir=(0.0, 1.0, 0.0))


def build_trial(report):
    floor = make_box(*FLOOR_X, *FLOOR_Y, *FLOOR_Z)
    root_barrel = cylinder_y(3.0, -64.0, 64.0)
    cheeks = [triangle_cheek(-64.0), triangle_cheek(62.0)]
    ramp_unbored = union([floor, root_barrel, *cheeks])
    ramp_cut = (ramp_unbored - cylinder_y(1.5, -64.0, 64.0)).clean()
    ramp_solids = list(ramp_cut.solids())
    ramp = ramp_solids[0] if len(ramp_solids) == 1 else ramp_cut

    mounts = []
    for name, y0, y1 in (
        ("fixed_mount_negative_y", -71.0, -65.0),
        ("fixed_mount_positive_y", 65.0, 71.0),
    ):
        foot = make_box(-953.0, -947.0, y0, y1, -83.0, -75.0)
        tube = cylinder_y(3.0, y0, y1)
        mount_cut = (union([tube, foot]) - cylinder_y(1.5, y0, y1)).clean()
        mount_solids = list(mount_cut.solids())
        bored = mount_solids[0] if len(mount_solids) == 1 else mount_cut
        bored.label = name
        mounts.append(bored)

    shaft = cylinder_y(1.25, -71.3, 71.3)
    cap_neg = cylinder_y(2.5, -72.0, -71.3)
    cap_pos = cylinder_y(2.5, 71.3, 72.0)
    pin = union([shaft, cap_neg, cap_pos])

    # The two cutters overlap by 0.3 mm in X.  The shaft bore crosses the
    # belly bay into both support stations; cap counterbores extend 0.3 mm
    # axially beyond each named cap interval.
    cavity = make_box(-953.3, -289.7, -64.3, 64.3, -100.0, -25.8)
    stub = make_box(-1030.0, -953.0, -58.0, 58.0, -77.0, -28.0)
    barrel_relief = cylinder_y(3.3, -64.3, 64.3)
    shaft_relief = cylinder_y(1.55, -71.3, 71.3)
    cap_reliefs = [
        cylinder_y(2.8, -72.3, -71.0),
        cylinder_y(2.8, 71.0, 72.3),
    ]
    body_cutters = union([cavity, stub, barrel_relief, shaft_relief, *cap_reliefs])

    scene_parts = r4check.flatten_step(INPUT_STEP)
    missing = sorted(set(EXPECTED_LABELS) - set(scene_parts))
    extra = sorted(set(scene_parts) - set(EXPECTED_LABELS))
    report["saved_input"] = {
        "path": str(INPUT_STEP),
        "part_count": len(scene_parts),
        "expected_part_count": len(EXPECTED_LABELS),
        "missing_labels": missing,
        "unexpected_labels": extra,
    }
    if missing or extra or len(scene_parts) != 29:
        raise RuntimeError(f"Saved STEP inventory mismatch: missing={missing}, extra={extra}, count={len(scene_parts)}")

    original_body = scene_parts[BODY]
    body_cut = (original_body - body_cutters).clean()
    body_solids = list(body_cut.solids())
    body = body_solids[0] if len(body_solids) == 1 else body_cut
    report["construction"] = {
        "moving_ramp": one_solid(ramp),
        "fixed_mount_negative_y": one_solid(mounts[0]),
        "fixed_mount_positive_y": one_solid(mounts[1]),
        "throughpin_with_caps": one_solid(pin),
        "body_after_only_named_cuts": one_solid(body),
        "body_cutter_union": one_solid(body_cutters),
        "ramp_unbored_fusion": one_solid(ramp_unbored),
        "body_cutters_mm": {
            "cavity_box": {"x": [-953.3, -289.7], "y": [-64.3, 64.3], "z": [-100.0, -25.8]},
            "aft_stub_box": {"x": [-1030.0, -953.0], "y": [-58.0, 58.0], "z": [-77.0, -28.0]},
            "moving_barrel_relief": {"radius_mm": 3.3, "y_mm": [-64.3, 64.3]},
            "pin_shaft_relief": {"radius_mm": 1.55, "y_mm": [-71.3, 71.3]},
            "pin_cap_reliefs": [
                {"radius_mm": 2.8, "y_mm": [-72.3, -71.0]},
                {"radius_mm": 2.8, "y_mm": [71.0, 72.3]},
            ],
            "stub_to_cavity_intersection_mm3": volume(stub & cavity),
            "cavity_stub_overlap_x_mm": 0.3,
        },
    }
    new_parts = {
        "ramp_moving_assembly": ramp,
        "fixed_mount_negative_y": mounts[0],
        "fixed_mount_positive_y": mounts[1],
        "hinge_throughpin": pin,
    }
    return scene_parts, original_body, body, body_cutters, new_parts


def moving_intake_pose(ramp, fraction):
    return ramp.rotate(
        bd.Axis((HINGE_X, 0.0, HINGE_Z), (0.0, 1.0, 0.0)),
        RAMP_ANGLE_DEG * fraction,
    )


def reconstruct_existing(scene_parts, body, fraction, canonical, station_axis_points):
    base = {label: scene_parts[label] for label in r4check.A5_LABELS}
    posed = a5check.move_saved_stowed(
        base, fraction, canonical, a5check.CUMULATIVE_A2_DROP_MM
    )
    posed[BODY] = body
    for station, _ in STATIONS:
        point = station_axis_points[station]
        for suffix in TAIL_SUFFIXES:
            label = f"tail_r4_{station}_{suffix}"
            part = scene_parts[label]
            if suffix == "fin_root" and fraction:
                part = part.rotate(
                    bd.Axis((point.X, point.Y, point.Z), (1.0, 0.0, 0.0)),
                    FOLD_ANGLE_DEG * fraction,
                )
            posed[label] = part
    return posed


def check_pair(first_label, first, second_label, second, fraction, report):
    pair = [first_label, second_label]
    lower_bound = bbox_gap(first, second)
    if lower_bound > MIN_CLEARANCE_MM:
        return {"pair": pair, "clearance_mm": lower_bound, "method": "disjoint_AABB_lower_bound",
                "overlap_mm3": 0.0, "pass": True}
    distance = float(closest_points(first, second).distance)
    overlap = float(overlap_volume(first, second)) if lower_bound == 0.0 else 0.0
    result = {
        "pair": pair,
        "clearance_mm": distance,
        "method": "exact_nearest_points_and_overlap" if lower_bound == 0.0 else "exact_nearest_points",
        "overlap_mm3": overlap,
        "pass": distance > MIN_CLEARANCE_MM and overlap < OVERLAP_TOL_MM3,
    }
    if not result["pass"]:
        report["failures"].append({
            "check": "intake_part_clearance_or_unexpected_overlap",
            "fraction": fraction,
            **result,
            "minimum_clearance_mm_exclusive": MIN_CLEARANCE_MM,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
        })
    return result


def radial_bbox_radius(shape):
    b = bounds(shape)
    return max(math.hypot(y, z) for y in b["y"] for z in b["z"])


def main():
    report = {
        "gate": "R1_belly_ramp_in_memory_intake_feasibility",
        "units": "mm",
        "scope": "In-memory trial geometry only; no model source, saved CAD artifact, or render changed.",
        "thresholds": {
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "moving_intake_clearance_mm_exclusive": MIN_CLEARANCE_MM,
            "fixed_mount_body_contact_mm3_exclusive": CONTACT_EPS_MM3,
            "new_solid_validity": "one valid positive-volume solid each",
            "stowed_radius_mm_exclusive": 125.0,
            "motion_sample_count": len(FRACTIONS),
        },
        "trial_dimensions_mm": {
            "floor_x": list(FLOOR_X), "floor_y": list(FLOOR_Y), "floor_z": list(FLOOR_Z),
            "hinge_axis_point": [HINGE_X, 0.0, HINGE_Z],
            "deployment_deg": ANGLE_DEG,
            "cheek_vertices_xz": [[-950.0, -83.0], [-300.0, -83.0],
                                  [-300.0, -83.0 + 650.0 * math.tan(math.radians(5.0))]],
            "cheek_y_intervals": [[-64.0, -62.0], [62.0, 64.0]],
            "early_motion_fractions": list(EARLY_FRACTIONS),
        },
        "failures": [],
    }
    try:
        scene_parts, original_body, body, body_cutters, new_parts = build_trial(report)
        report["construction"]["source_body_topology"] = one_solid(original_body)
        for label, shape in {**scene_parts, **new_parts, BODY: body}.items():
            if label in EXPECTED_LABELS and not one_solid(shape)["pass"]:
                report["failures"].append({"check": "saved_or_cut_existing_part_topology",
                                           "label": label, "topology": one_solid(shape)})
        for label, topology in report["construction"].items():
            if isinstance(topology, dict) and "pass" in topology and not topology["pass"]:
                report["failures"].append({"check": "new_geometry_or_body_topology",
                                           "label": label, "topology": topology})

        contacts = {}
        for label in ("fixed_mount_negative_y", "fixed_mount_positive_y"):
            amount = float(overlap_volume(new_parts[label], body))
            contacts[label] = {"body_overlap_mm3": amount,
                               "positive_contact": amount > CONTACT_EPS_MM3}
            if amount <= CONTACT_EPS_MM3:
                report["failures"].append({"check": "fixed_mount_body_support_contact",
                                           "pair": [label, BODY], "overlap_mm3": amount,
                                           "minimum_mm3_exclusive": CONTACT_EPS_MM3})
        report["fixed_mount_contacts"] = contacts

        stowed = new_parts["ramp_moving_assembly"]
        floor_outerface = float(bounds(stowed)["z"][0])
        flush_error = abs(floor_outerface - FLOOR_Z[0])
        report["stowed_flush"] = {
            "ramp_assembly_outermost_z_mm": floor_outerface,
            "nominal_belly_face_z_mm": BODY_BELLY_Z,
            "absolute_flush_error_mm": flush_error,
            "pass": flush_error <= 1.0e-6,
        }
        if flush_error > 1.0e-6:
            report["failures"].append({"check": "stowed_outer_face_flush_to_belly_datum",
                                       **report["stowed_flush"]})

        body_cuts_valid = report["construction"]["body_cutter_union"]["pass"]
        body_valid = report["construction"]["body_after_only_named_cuts"]["pass"]
        report["body_connectivity"] = {
            "cavity_stub_overlap_x_mm": 0.3,
            "cavity_stub_intersection_volume_mm3": report["construction"]["body_cutters_mm"]["stub_to_cavity_intersection_mm3"],
            "connected_cut_volume_single_solid": body_cuts_valid,
            "cut_body_remains_one_valid_solid": body_valid,
            "cut_body_volume_mm3": volume(body),
            "removed_body_volume_mm3": volume(original_body) - volume(body),
            "pass": body_cuts_valid and body_valid,
        }
        if not report["body_connectivity"]["pass"]:
            report["failures"].append({"check": "body_cut_connectivity_or_body_solid"})

        full_stowed = {**scene_parts, BODY: body, **new_parts}
        per_part_radius = {label: radial_bbox_radius(shape) for label, shape in full_stowed.items()}
        radius_witness = max(per_part_radius, key=per_part_radius.get)
        report["stowed_envelope"] = {
            "part_count_including_4_new_parts": len(full_stowed),
            "conservative_bbox_corner_radius_mm_by_part": per_part_radius,
            "maximum_radius_mm": per_part_radius[radius_witness],
            "witness": radius_witness,
            "limit_mm_exclusive": 125.0,
            "pass": len(full_stowed) == 33 and per_part_radius[radius_witness] < 125.0,
        }
        if not report["stowed_envelope"]["pass"]:
            report["failures"].append({"check": "stowed_125mm_envelope",
                                       **report["stowed_envelope"]})

        # Require that local A5 panels/supports are in the saved R4 assembly,
        # then use the identical saved-pose motion reconstruction as the R4 checker.
        needed = set(a5check.PANELS) | set(a5check.SUPPORTS)
        missing = sorted(needed - set(scene_parts))
        if missing:
            raise RuntimeError(f"Saved R4 Stowed lacks A5 motion-helper inputs: {missing}")
        canonical = {
            label: a5check.panel_canonical(
                scene_parts[label], *label.split("_"), a5check.CUMULATIVE_A2_DROP_MM
            )
            for label in a5check.PANELS
        }
        station_axis_points = {
            station: r4check.rotate_x(bd.Vertex(0.0, 82.0, 83.0), angle).center()
            for station, angle in STATIONS
        }

        sample_rows = []
        minimum = {"clearance_mm": None, "pair": None, "fraction": None}
        maximum_overlap = {"overlap_mm3": 0.0, "pair": None, "fraction": None}
        moving_labels = tuple(new_parts)
        for sample_index, fraction in enumerate(FRACTIONS):
            existing = reconstruct_existing(scene_parts, body, fraction, canonical, station_axis_points)
            posed_new = dict(new_parts)
            posed_new["ramp_moving_assembly"] = moving_intake_pose(
                new_parts["ramp_moving_assembly"], fraction
            )
            checks = []
            for new_label, new_shape in posed_new.items():
                for existing_label, existing_shape in existing.items():
                    if frozenset((new_label, existing_label)) in MOUNT_BODY_PAIRS:
                        continue
                    row = check_pair(new_label, new_shape, existing_label, existing_shape,
                                     fraction, report)
                    checks.append(row)
                    if row["clearance_mm"] < MIN_CLEARANCE_MM:
                        if minimum["clearance_mm"] is None or row["clearance_mm"] < minimum["clearance_mm"]:
                            minimum = {"clearance_mm": row["clearance_mm"],
                                       "pair": row["pair"], "fraction": fraction}
                    if row["overlap_mm3"] > maximum_overlap["overlap_mm3"]:
                        maximum_overlap = {"overlap_mm3": row["overlap_mm3"],
                                           "pair": row["pair"], "fraction": fraction}
            for (first_label, first), (second_label, second) in itertools.combinations(posed_new.items(), 2):
                row = check_pair(first_label, first, second_label, second, fraction, report)
                checks.append(row)
                if row["clearance_mm"] < MIN_CLEARANCE_MM:
                    if minimum["clearance_mm"] is None or row["clearance_mm"] < minimum["clearance_mm"]:
                        minimum = {"clearance_mm": row["clearance_mm"],
                                   "pair": row["pair"], "fraction": fraction}
                if row["overlap_mm3"] > maximum_overlap["overlap_mm3"]:
                    maximum_overlap = {"overlap_mm3": row["overlap_mm3"],
                                       "pair": row["pair"], "fraction": fraction}
            sample_minimum = min(checks, key=lambda row: row["clearance_mm"])
            if (minimum["clearance_mm"] is None
                    or sample_minimum["clearance_mm"] < minimum["clearance_mm"]):
                minimum = {
                    "clearance_mm": sample_minimum["clearance_mm"],
                    "pair": sample_minimum["pair"],
                    "fraction": fraction,
                    "method": sample_minimum["method"],
                }
            sample_rows.append({
                "sample": sample_index,
                "fraction": fraction,
                "ramp_angle_deg": RAMP_ANGLE_DEG * fraction,
                "existing_tail_fold_angle_deg": FOLD_ANGLE_DEG * fraction,
                "new_part_count": len(posed_new),
                "existing_part_count": len(existing),
                "nonexempt_pair_checks": len(checks),
                "all_pair_checks_pass": all(row["pass"] for row in checks),
                "minimum_clearance_mm": min((row["clearance_mm"] for row in checks), default=None),
            })
        report["motion"] = {
            "method": "66 synchronous cross-samples against saved R4 parts, using the existing A5 saved-pose helper; intake ramp +5deg*f and R4 fin fold -135deg*f",
            "sample_count": len(sample_rows),
            "expected_sample_count": 66,
            "uniform_sample_count": 61,
            "early_fractions": list(EARLY_FRACTIONS),
            "new_part_count": 4,
            "existing_part_count_per_sample": 29,
            "minimum_sampled_clearance": minimum,
            "maximum_unexpected_overlap": maximum_overlap,
            "all_samples_pass": len(sample_rows) == 66 and all(row["all_pair_checks_pass"] for row in sample_rows),
            "samples": sample_rows,
        }

        # At x=-305 the ramp top is the transformed local z=-83 floor face.
        mouth_x = -305.0
        mouth_floor_top_z = HINGE_Z - math.tan(math.radians(ANGLE_DEG)) * (mouth_x - HINGE_X)
        mouth_z0 = mouth_floor_top_z + 0.3
        mouth_z1 = BODY_BELLY_Z - 0.3
        mouth_y0, mouth_y1 = -62.0, 62.0
        mouth_test = make_box(mouth_x - 0.1, mouth_x + 0.1, mouth_y0, mouth_y1, mouth_z0, mouth_z1)
        mouth_test_solid = list(mouth_test.solids())[0]
        mouth_blockers = []
        posed_deployed = dict(new_parts)
        posed_deployed["ramp_moving_assembly"] = moving_intake_pose(new_parts["ramp_moving_assembly"], 1.0)
        deployed_existing = reconstruct_existing(scene_parts, body, 1.0, canonical, station_axis_points)
        for label, shape in {**deployed_existing, **posed_deployed}.items():
            amount = (float(overlap_volume(mouth_test_solid, shape))
                      if bbox_gap(mouth_test_solid, shape) == 0.0 else 0.0)
            if amount >= OVERLAP_TOL_MM3:
                mouth_blockers.append({"label": label, "overlap_mm3": amount})
        mouth_height = mouth_z1 - mouth_z0
        mouth_width = mouth_y1 - mouth_y0
        report["deployed_mouth"] = {
            "test_plane_x_mm": mouth_x,
            "test_slab_x_mm": [mouth_x - 0.1, mouth_x + 0.1],
            "z_between_floor_plus_0_3_and_belly_minus_0_3_mm": [mouth_z0, mouth_z1],
            "y_between_cheek_inner_faces_mm": [mouth_y0, mouth_y1],
            "floor_top_at_test_plane_z_mm": mouth_floor_top_z,
            "unobstructed_height_mm": mouth_height,
            "unobstructed_width_mm": mouth_width,
            "test_volume_mm3": volume(mouth_test),
            "blockers_ge_0_001_mm3": mouth_blockers,
            "pass": mouth_height > 0.0 and mouth_width > 0.0 and not mouth_blockers,
            "interpretation": "Geometric open-mouth volume only; not CFD or an airflow-performance claim.",
        }
        if not report["deployed_mouth"]["pass"]:
            report["failures"].append({"check": "deployed_forward_mouth_open", **report["deployed_mouth"]})

        report["passed"] = not report["failures"]
        report["summary"] = {
            "passed": report["passed"],
            "failure_count": len(report["failures"]),
            "saved_part_count": report["saved_input"]["part_count"],
            "new_solid_count": len(new_parts),
            "motion_sample_count": len(sample_rows),
            "minimum_sampled_clearance": minimum,
            "maximum_unexpected_overlap": maximum_overlap,
            "mouth_height_mm": mouth_height,
            "mouth_width_mm": mouth_width,
            "stowed_radius_mm": report["stowed_envelope"]["maximum_radius_mm"],
            "body_single_solid": body_valid,
        }
    except Exception as exc:
        report["passed"] = False
        report["failures"].append({
            "check": "probe_aborted_on_measured_exception",
            "error": repr(exc),
            "traceback": traceback.format_exc(),
        })
        report["summary"] = {
            "passed": False,
            "failure_count": len(report["failures"]),
            "saved_part_count": report.get("saved_input", {}).get("part_count"),
            "motion_sample_count": len(report.get("motion", {}).get("samples", [])),
        }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT_PATH),
        **report.get("summary", {}),
        "failed_checks": [failure["check"] for failure in report["failures"]],
        "first_failures": report["failures"][:12],
    }, indent=2))
    return 0 if report.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
