"""One-corner R3 aft-fin recess feasibility probe; does not rebuild production CAD."""

from __future__ import annotations

import json
import math
import sys
import traceback
from pathlib import Path

import build123d as bd
from cadgen.geometry import closest_points, overlap_volume


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reviews" / "tail_fin_r3_probe.json"
BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
FIN_LABEL = "tail_r1_fin_root"
SUPPORT_LABELS = ("tail_r1_fixed_knuckle_aft", "tail_r1_fixed_knuckle_forward")
PIN_LABEL = "tail_r1_throughpin"
TAIL_LABELS = (FIN_LABEL, *SUPPORT_LABELS, PIN_LABEL)
A5_LABELS = (
    BODY_LABEL,
    "port_carriage", "port_fixed_root", "port_front", "port_join", "port_rear",
    "starboard_carriage", "starboard_fixed_root", "starboard_front", "starboard_join", "starboard_rear",
    "supported_housing", "top_cover",
)
SHIFT_X = -80.0
ROOT_X = (-1325.0, -1085.0)
HINGE_Y = 82.0
HINGE_Z = 83.0
FOLD_DEG = -135.0
PANEL_Z = (83.0, 86.0)
POCKET_Z = (82.7, 100.0)
POCKET_OFFSET = 0.3
BODY_CLEARANCE = 0.2
OVERLAP_TOL = 0.001
CONTACT_TOL = 1.0e-5
BASE_TOP_Z_EXPECTED = 86.0
RADIAL_LIMIT = 125.0
X_TOL = 0.01
FOLD_SAMPLES = tuple(sorted(set(i / 60.0 for i in range(61)) | {0.001, 0.002, 0.005, 0.01, 0.02}))
IDENTITY_AXIS = bd.Axis((0.0, HINGE_Y, HINGE_Z), (1.0, 0.0, 0.0))


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


def topology(shape):
    solids = list(shape.solids())
    volumes = [float(solid.volume) for solid in solids]
    return {
        "valid": bool(shape.is_valid),
        "solid_count": len(solids),
        "positive_volumes_mm3": volumes,
        "pass": bool(shape.is_valid and len(solids) == 1 and volumes and all(value > 0.0 for value in volumes)),
    }


def as_solid(shape):
    solids = list(shape.solids())
    if len(solids) != 1:
        raise RuntimeError(f"Expected one solid for pairwise geometry check, found {len(solids)}")
    return solids[0]


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
    result = {}
    duplicates = []
    for part in leaves:
        label = str(part.label)
        if label in result:
            duplicates.append(label)
        solids = list(part.solids())
        if len(solids) == 1:
            solids[0].label = label
            result[label] = solids[0]
        else:
            result[label] = part
    if duplicates:
        raise RuntimeError(f"Duplicate saved STEP labels in {path}: {duplicates}")
    return result


def cylinder_x(radius, x0, x1, y, z):
    return bd.Cylinder(
        radius,
        x1 - x0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER),
    ).rotate(bd.Axis.Y, 90.0).translate(((x0 + x1) / 2.0, y, z))


def exact_minimum(pairs):
    candidates = sorted((bbox_gap(first, second), name, first, second) for name, first, second in pairs)
    best = math.inf
    witness = None
    exact_count = 0
    overlaps = []
    for lower_bound, name, first, second in candidates:
        if lower_bound > best:
            break
        first_solid, second_solid = as_solid(first), as_solid(second)
        overlap = float(overlap_volume(first_solid, second_solid))
        distance = float(closest_points(first_solid, second_solid).distance)
        exact_count += 1
        if overlap >= OVERLAP_TOL:
            overlaps.append({"pair": name, "overlap_mm3": overlap})
        if distance < best:
            best, witness = distance, name
    return {
        "minimum_clearance_mm": None if math.isinf(best) else best,
        "witness_pair": witness,
        "exact_pairs_tested": exact_count,
        "AABB_pairs_pruned": len(candidates) - exact_count,
        "unexpected_overlaps_ge_0_001_mm3": overlaps,
        "pass": best > BODY_CLEARANCE and not overlaps,
    }


def make_fin(planform):
    points = [(x + SHIFT_X, HINGE_Y - inward_span, PANEL_Z[0]) for x, inward_span in planform]
    panel = bd.extrude(
        bd.Face(bd.Wire.make_polygon(points, close=True)),
        amount=PANEL_Z[1] - PANEL_Z[0],
        dir=(0, 0, 1),
    )
    root_tube = cylinder_x(3.0, *ROOT_X, HINGE_Y, HINGE_Z)
    bore = cylinder_x(1.5, ROOT_X[0] - 0.1, ROOT_X[1] + 0.1, HINGE_Y, HINGE_Z)
    fin = ((panel + root_tube).clean() - bore).clean()
    fin.label = FIN_LABEL
    return fin


def read_pin_cylinder_bounds(pin):
    shaft_faces = []
    cap_faces = []
    for face in pin.faces():
        if face.geom_type != bd.GeomType.CYLINDER:
            continue
        face_bounds = bounds(face)
        radius = float(face.radius)
        row = {"radius_mm": radius, **face_bounds}
        if abs(radius - 1.25) < 1.0e-6:
            shaft_faces.append(row)
        elif abs(radius - 2.5) < 1.0e-6:
            cap_faces.append(row)
    if len(shaft_faces) != 1 or len(cap_faces) != 2:
        raise RuntimeError(f"Cannot uniquely identify saved R2 pin shaft/caps: shaft={shaft_faces}, caps={cap_faces}")
    shaft_x = shaft_faces[0]["x"]
    cap_x = sorted((row["x"] for row in cap_faces), key=lambda pair: pair[0])
    if abs(shaft_x[0] - (-1335.3)) > X_TOL or abs(shaft_x[1] - (-1074.7)) > X_TOL:
        raise RuntimeError(f"Measured saved R2 pin shaft bounds differ from expected after -80 X / -5.5 Z: {shaft_x}")
    return {"shaft_cylindrical_face": shaft_faces[0], "cap_cylindrical_faces": cap_faces,
            "shaft_x_mm": shaft_x, "cap_intervals_x_mm": cap_x}


def main():
    sys.path.insert(0, str(ROOT / "src"))
    import tail_fin_r1
    import check_interleaved_a5 as a5check

    r2_path = ROOT / "STEP" / "Q_Tail_R2_Clipped_Stowed.step"
    a5_path = ROOT / "STEP" / "O_Interleaved_A5_Stowed.step"
    r2_parts = flatten_step(r2_path)
    a5_parts = flatten_step(a5_path)
    missing_r2 = sorted(set(TAIL_LABELS) - set(r2_parts))
    missing_a5 = sorted(set(A5_LABELS) - set(a5_parts))
    if missing_r2 or missing_a5:
        raise RuntimeError(f"Missing saved R2/A5 parts: R2={missing_r2}, A5={missing_a5}")

    # The saved R2 parts are immutable references; only this probe's copies move down 5.5 mm.
    supports = {label: r2_parts[label].translate((0.0, 0.0, -5.5)) for label in SUPPORT_LABELS}
    pin = r2_parts[PIN_LABEL].translate((0.0, 0.0, -5.5))
    pin_bounds = read_pin_cylinder_bounds(pin)
    planform = tail_fin_r1.PLANFORMS["Tall"]
    fin_stowed = make_fin(planform)
    tail = {FIN_LABEL: fin_stowed, **supports, PIN_LABEL: pin}

    # Native Wire.offset_2d expands the closed clockwise XY loop outward for a positive distance.
    outline_points = [(x + SHIFT_X, HINGE_Y - span, 0.0) for x, span in planform]
    outline = bd.Wire.make_polygon(outline_points, close=True)
    offset_outline = outline.offset_2d(
        POCKET_OFFSET,
        kind=bd.Kind.ARC,
        side=bd.Side.BOTH,
        closed=True,
    )
    offset_area = float(bd.Face(offset_outline).area)
    original_area = float(bd.Face(outline).area)
    offset_bounds = bounds(offset_outline)
    if offset_area <= original_area:
        raise RuntimeError("Native offset did not enlarge the panel outline; no fallback well is permitted")

    broad_pocket = bd.extrude(
        bd.Face(offset_outline),
        amount=POCKET_Z[1] - POCKET_Z[0],
        dir=(0, 0, 1),
    ).translate((0.0, 0.0, POCKET_Z[0]))
    hinge_relief = cylinder_x(3.3, ROOT_X[0] - 0.3, ROOT_X[1] + 0.3, HINGE_Y, HINGE_Z)
    shaft_x = pin_bounds["shaft_x_mm"]
    shaft_relief = cylinder_x(1.55, shaft_x[0] - 0.3, shaft_x[1] + 0.3, HINGE_Y, HINGE_Z)
    cap_reliefs = [
        cylinder_x(2.8, interval[0] - 0.3, interval[1] + 0.3, HINGE_Y, HINGE_Z)
        for interval in pin_bounds["cap_intervals_x_mm"]
    ]
    cutters = [broad_pocket, hinge_relief, shaft_relief, *cap_reliefs]
    cutter_union = cutters[0]
    for cutter in cutters[1:]:
        cutter_union = cutter_union + cutter
    cutter_union = cutter_union.clean()

    body = a5_parts[BODY_LABEL]
    body_bounds = bounds(body)
    recessed_body = (body - cutter_union).clean()
    removed = (body - recessed_body).clean()
    expected_removed = (body & cutter_union).clean()
    removed_symdiff = float((removed - expected_removed).volume) + float((expected_removed - removed).volume)
    fin_top = bounds(fin_stowed)["z"][1]
    hardware_top = max(bounds(supports[label])["z"][1] for label in SUPPORT_LABELS)
    hardware_top = max(hardware_top, bounds(pin)["z"][1])

    topology_results = {label: topology(shape) for label, shape in tail.items()}
    body_topology = topology(recessed_body)
    contact = {}
    for label, (x0, x1) in zip(SUPPORT_LABELS, ((-1335.0, -1326.0), (-1084.0, -1075.0))):
        support = supports[label]
        foot_box = bd.Solid.make_box(x1 - x0, 5.5, 8.5, plane=bd.Plane(origin=(x0, 79.0, 74.5)))
        foot = (support & foot_box).clean()
        knuckle = (support - foot_box).clean()
        foot_overlap = float(overlap_volume(foot, recessed_body))
        knuckle_overlap = float(overlap_volume(knuckle, recessed_body))
        contact[label] = {
            "foot_body_overlap_mm3": foot_overlap,
            "knuckle_body_overlap_mm3": knuckle_overlap,
            "combined_support_body_overlap_mm3": float(overlap_volume(support, recessed_body)),
            "foot_positive_attachment": foot_overlap > CONTACT_TOL,
            "knuckle_positive_attachment": knuckle_overlap > CONTACT_TOL,
        }

    # The A5 helper reconstructs the approved saved-stowed moving parts at every trial fraction.
    canonical_panels = {}
    for label in a5check.PANELS:
        side, kind = label.split("_")
        canonical_panels[label] = a5check.panel_canonical(
            a5_parts[label], side, kind, a5check.CUMULATIVE_A2_DROP_MM
        )

    hardware_pairs = []
    for index, first_label in enumerate((*SUPPORT_LABELS, PIN_LABEL)):
        for second_label in (*SUPPORT_LABELS, PIN_LABEL)[index + 1:]:
            hardware_pairs.append((f"{first_label}:{second_label}", tail[first_label], tail[second_label]))
    static_hardware_interactions = exact_minimum(hardware_pairs)
    motion_rows = []
    all_motion_failures = []
    all_clearances = []
    all_unexpected_overlaps = []

    for sample_index, fraction in enumerate(FOLD_SAMPLES):
        posed_a5 = a5check.move_saved_stowed(
            a5_parts, fraction, canonical_panels, a5check.CUMULATIVE_A2_DROP_MM
        )
        posed_a5[BODY_LABEL] = recessed_body
        angle = FOLD_DEG * fraction
        moving_fin = fin_stowed.rotate(IDENTITY_AXIS, angle) if fraction else fin_stowed
        moving_fin.label = FIN_LABEL
        fin_pairs = [(f"hardware:{label}", moving_fin, tail[label]) for label in (*SUPPORT_LABELS, PIN_LABEL)]
        fin_pairs.extend((f"A5:{label}", moving_fin, posed_a5[label]) for label in A5_LABELS)
        fin_result = exact_minimum(fin_pairs)
        all_clearances.append((fin_result["minimum_clearance_mm"], fin_result["witness_pair"], fraction, "moving_fin"))
        all_unexpected_overlaps.extend(
            {**row, "fraction": fraction, "angle_deg": angle, "component": "moving_fin"}
            for row in fin_result["unexpected_overlaps_ge_0_001_mm3"]
        )

        pin_pairs = [(f"A5:{label}", pin, posed_a5[label]) for label in A5_LABELS]
        pin_pairs.extend((f"hardware:{label}", pin, supports[label]) for label in SUPPORT_LABELS)
        pin_result = exact_minimum(pin_pairs)
        all_clearances.append((pin_result["minimum_clearance_mm"], pin_result["witness_pair"], fraction, "through_pin"))
        all_unexpected_overlaps.extend(
            {**row, "fraction": fraction, "angle_deg": angle, "component": "through_pin"}
            for row in pin_result["unexpected_overlaps_ge_0_001_mm3"]
        )

        support_results = {}
        for label in SUPPORT_LABELS:
            pairs = [(f"A5:{name}", supports[label], posed_a5[name]) for name in A5_LABELS if name != BODY_LABEL]
            pairs.append((f"hardware:{PIN_LABEL}", supports[label], pin))
            pairs.extend((f"hardware:{other}", supports[label], supports[other]) for other in SUPPORT_LABELS if other != label)
            result = exact_minimum(pairs)
            support_results[label] = result
            all_clearances.append((result["minimum_clearance_mm"], result["witness_pair"], fraction, label))
            all_unexpected_overlaps.extend(
                {**row, "fraction": fraction, "angle_deg": angle, "component": label}
                for row in result["unexpected_overlaps_ge_0_001_mm3"]
            )

        sample_pass = (
            fin_result["pass"] and pin_result["pass"]
            and all(result["pass"] for result in support_results.values())
        )
        if not sample_pass:
            all_motion_failures.append({
                "sample": sample_index,
                "fraction": fraction,
                "angle_deg": angle,
                "fin": fin_result,
                "pin": pin_result,
                "supports": support_results,
            })
        motion_rows.append({
            "sample": sample_index,
            "fraction": fraction,
            "angle_deg": angle,
            "moving_fin_vs_hardware_and_A5": fin_result,
            "pin_vs_A5_and_supports": pin_result,
            "fixed_supports_vs_A5_and_hardware": support_results,
            "pass": sample_pass,
        })

    radial = {
        label: math.hypot(max(abs(bounds(shape)["y"][0]), abs(bounds(shape)["y"][1])),
                          max(abs(bounds(shape)["z"][0]), abs(bounds(shape)["z"][1])))
        for label, shape in tail.items()
    }
    minimum_clearance = min((row[0], row[1], row[2], row[3]) for row in all_clearances if row[0] is not None)
    broad_depth = body_bounds["z"][1] - POCKET_Z[0]
    hinge_depth = body_bounds["z"][1] - (HINGE_Z - 3.3)
    pass_checks = {
        "stowed_panel_outer_face_Z86": abs(fin_top - 86.0) <= X_TOL,
        "hardware_max_Z86": abs(hardware_top - 86.0) <= X_TOL,
        "body_is_valid_single_positive_solid": body_topology["pass"],
        "all_four_tail_parts_valid_single_positive_solids": all(row["pass"] for row in topology_results.values()),
        "body_removed_only_by_declared_cutters": removed_symdiff < 0.01,
        "body_pocket_depth_3_3_mm": abs(broad_depth - 3.3) <= X_TOL,
        "root_relief_depth_6_3_mm": abs(hinge_depth - 6.3) <= X_TOL,
        "offset_is_outward_0_3_mm": offset_area > original_area and len(offset_outline.edges()) >= 4,
        "saved_R2_pin_shaft_bounds_verified": True,
        "fixed_foot_body_positive_attachments": all(row["foot_positive_attachment"] for row in contact.values()),
        "fixed_knuckles_positive_body_attachments": all(row["knuckle_positive_attachment"] for row in contact.values()),
        "stowed_tail_radius_below_125_mm": max(radial.values()) < RADIAL_LIMIT,
        "all_tail_motion_samples_clear_over_0_2_mm": len(motion_rows) >= 61 and not all_motion_failures,
        "fixed_hardware_mutual_clearance_over_0_2_mm": static_hardware_interactions["pass"],
        "no_unexpected_overlap_ge_0_001_mm3": not all_unexpected_overlaps,
    }
    overall_pass = all(pass_checks.values())
    report = {
        "gate": "TailR3 aft-shifted clipped-fin local recess feasibility",
        "units": "mm",
        "scope": "In-memory geometry probe only; saved A5 body and R2 hardware are read-only; no production source/build/render.",
        "thresholds": {
            "clearance_mm_exclusive": BODY_CLEARANCE,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL,
            "positive_attachment_overlap_mm3_exclusive": CONTACT_TOL,
            "radial_bound_mm_exclusive": RADIAL_LIMIT,
            "fold_samples": list(FOLD_SAMPLES),
        },
        "source_inputs": {
            "R1_planform_source": str(ROOT / "src" / "tail_fin_r1.py"),
            "saved_R2_stowed": str(r2_path),
            "saved_A5_stowed": str(a5_path),
            "A5_motion_helper": str(ROOT / "src" / "check_interleaved_a5.py"),
        },
        "panel_and_hardware": {
            "panel_planform_xy_mm": [[x + SHIFT_X, HINGE_Y - span] for x, span in planform],
            "panel_z_mm": list(PANEL_Z),
            "panel_outer_face_z_mm": fin_top,
            "root_tube_axis_yz_mm": [HINGE_Y, HINGE_Z],
            "root_tube_radius_mm": 3.0,
            "pin_bore_radius_mm": 1.5,
            "hardware_max_z_mm": hardware_top,
            "saved_R2_pin_cylinders_after_Z_drop_5_5": pin_bounds,
            "body_before_bounds_mm": body_bounds,
            "tail_topology": topology_results,
            "body_after_topology": body_topology,
            "tail_bounds_mm": {label: bounds(shape) for label, shape in tail.items()},
            "stowed_conservative_YZ_radius_mm": radial,
            "fixed_support_body_contacts": contact,
        },
        "local_pocket": {
            "method": "single shaped XY panel outline expanded by native Wire.offset_2d(0.3), plus coaxial cylindrical hinge/pin/cap reliefs",
            "offset_outline_bounds_mm": offset_bounds,
            "offset_original_area_mm2": original_area,
            "offset_area_mm2": offset_area,
            "specified_cutters": [
                {"name": "outline-pocket", "bounds_mm": bounds(broad_pocket)},
                {"name": "hinge-relief", "bounds_mm": bounds(hinge_relief), "radius_mm": 3.3},
                {"name": "pin-shaft-relief", "bounds_mm": bounds(shaft_relief), "radius_mm": 1.55},
                *[{"name": f"pin-cap-relief-{index + 1}", "bounds_mm": bounds(cutter), "radius_mm": 2.8}
                  for index, cutter in enumerate(cap_reliefs)],
            ],
            "body_bbox_top_z_mm": body_bounds["z"][1],
            "outline_pocket_depth_mm": broad_depth,
            "root_relief_depth_mm": hinge_depth,
            "body_removed_volume_mm3": float(removed.volume),
            "body_intersection_with_declared_cutters_mm3": float(expected_removed.volume),
            "removed_region_symmetric_difference_mm3": removed_symdiff,
        },
        "static_fixed_hardware_interactions": static_hardware_interactions,
        "motion": {
            "sample_count": len(motion_rows),
            "minimum_exact_clearance_mm": minimum_clearance[0],
            "minimum_clearance_witness_pair": minimum_clearance[1],
            "minimum_clearance_fraction": minimum_clearance[2],
            "minimum_clearance_component": minimum_clearance[3],
            "failing_samples": all_motion_failures,
            "unexpected_overlaps_ge_0_001_mm3": all_unexpected_overlaps,
            "samples": motion_rows,
        },
        "checks": pass_checks,
        "passed": overall_pass,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT_PATH),
        "passed": overall_pass,
        "failed_checks": [name for name, passed in pass_checks.items() if not passed],
        "sample_count": len(motion_rows),
        "minimum_clearance_mm": minimum_clearance[0],
        "minimum_clearance_witness_pair": minimum_clearance[1],
        "minimum_clearance_fraction": minimum_clearance[2],
        "support_contacts": contact,
        "body_removed_volume_mm3": float(removed.volume),
    }, indent=2))
    return 0 if overall_pass else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        failure = {
            "gate": "TailR3 aft-shifted clipped-fin local recess feasibility",
            "units": "mm",
            "passed": False,
            "error": repr(exc),
            "traceback": traceback.format_exc(),
        }
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(REPORT_PATH), "passed": False, "error": repr(exc)}, indent=2))
        raise SystemExit(2)
