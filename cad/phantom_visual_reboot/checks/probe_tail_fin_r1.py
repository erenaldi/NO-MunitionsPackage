"""One-corner R1 rear-fin feasibility probe against immutable saved A5 STEP."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_scene, read_step
from cadgen.geometry import closest_points, overlap_volume, topology_errors


ROOT = Path(__file__).resolve().parents[1]
BODY_STEP = ROOT / "STEP" / "O_Interleaved_A5_Body_Pocket.step"
ASSEMBLY_STEP = ROOT / "STEP" / "O_Interleaved_A5_Stowed.step"
REPORT = ROOT / "reviews" / "tail_fin_r1_probe.json"

HINGE_Y = 82.0
HINGE_Z = 88.5
FOLD_ANGLE_DEG = -135.0
PANEL_Z = (87.0, 90.0)
PANEL_PLANFORM = (
    (-1245.0, 0.0),
    (-1005.0, 0.0),
    (-1100.0, 110.0),
    (-1200.0, 110.0),
)
ROOT_X = (-1245.0, -1005.0)
FIXED_X = ((-1255.0, -1246.0), (-1004.0, -995.0))
PIN_SHAFT_X = (-1255.3, -994.7)
CAP_X = ((-1256.0, -1255.3), (-994.7, -994.0))
BORE_RADIUS = 1.5
PIN_RADIUS = 1.25
CAP_RADIUS = 2.5
SAMPLES = 31
MIN_CLEARANCE = 0.2
CONTACT_EPS_MM3 = 1.0e-5
OVERLAP_EPS_MM3 = 1.0e-5
X_LIMITS = (-1400.0, 1400.0)


def cylinder_x(radius: float, x0: float, x1: float, y: float, z: float):
    """Centered cylinder with its axis along X and endpoints x0/x1."""
    shape = bd.Cylinder(
        radius,
        x1 - x0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER),
    )
    return shape.rotate(bd.Axis.Y, 90.0).translate(((x0 + x1) / 2.0, y, z))


def bbox_data(shape):
    box = shape.bounding_box(optimal=False)
    return {
        "min": [float(box.min.X), float(box.min.Y), float(box.min.Z)],
        "max": [float(box.max.X), float(box.max.Y), float(box.max.Z)],
    }


def bbox_gap(a, b) -> float:
    ba, bb = bbox_data(a), bbox_data(b)
    gaps = []
    for axis in range(3):
        gaps.append(max(0.0, ba["min"][axis] - bb["max"][axis], bb["min"][axis] - ba["max"][axis]))
    return math.sqrt(sum(gap * gap for gap in gaps))


def solids(shape):
    return list(shape.solids())


def describe_shape(shape):
    bb = bbox_data(shape)
    return {
        "solid_count": len(solids(shape)),
        "volume_mm3": float(shape.volume),
        "bbox_mm": bb,
    }


def signature(shape):
    result = []
    for solid in solids(shape):
        bb = bbox_data(solid)
        result.append((
            round(float(solid.volume), 5),
            tuple(round(v, 5) for v in bb["min"]),
            tuple(round(v, 5) for v in bb["max"]),
        ))
    return tuple(sorted(result))


def radial_bound(shape) -> float:
    bb = bbox_data(shape)
    y = max(abs(bb["min"][1]), abs(bb["max"][1]))
    z = max(abs(bb["min"][2]), abs(bb["max"][2]))
    return math.hypot(y, z)


def build_geometry():
    # Panel points map (X, inward span) to Y=82-v; the unrotated thickness is Z=87..90.
    profile_points = [(x, HINGE_Y - v, PANEL_Z[0]) for x, v in PANEL_PLANFORM]
    panel_face = bd.Face(bd.Wire.make_polygon(profile_points, close=True))
    panel = bd.extrude(panel_face, amount=PANEL_Z[1] - PANEL_Z[0], dir=(0, 0, 1))
    root_tube = cylinder_x(3.0, *ROOT_X, HINGE_Y, HINGE_Z)
    moving_blank = (panel + root_tube).clean()
    moving_fin = (
        moving_blank - cylinder_x(BORE_RADIUS, ROOT_X[0] - 0.1, ROOT_X[1] + 0.1, HINGE_Y, HINGE_Z)
    ).clean()
    moving_fin.label = "tall_fin_and_root_tube"

    fixed_parts = []
    fixed_feet = []
    fixed_knuckles = []
    for index, (x0, x1) in enumerate(FIXED_X, start=1):
        foot = bd.Solid.make_box(
            x1 - x0,
            84.5 - 79.0,
            88.5 - 80.0,
            plane=bd.Plane(origin=(x0, 79.0, 80.0)),
        )
        knuckle = cylinder_x(3.0, x0, x1, HINGE_Y, HINGE_Z)
        fused = (foot + knuckle).clean()
        bore = cylinder_x(BORE_RADIUS, x0 - 0.1, x1 + 0.1, HINGE_Y, HINGE_Z)
        fixed = (fused - bore).clean()
        fixed.label = f"fixed_knuckle_foot_{index}"
        # Keep these cut sub-shapes only for classifying the required intentional contact.
        fixed_feet.append((foot - bore).clean())
        fixed_knuckles.append((knuckle - bore).clean())
        fixed_parts.append(fixed)

    shaft = cylinder_x(PIN_RADIUS, *PIN_SHAFT_X, HINGE_Y, HINGE_Z)
    caps = [cylinder_x(CAP_RADIUS, x0, x1, HINGE_Y, HINGE_Z) for x0, x1 in CAP_X]
    pin = (shaft + caps[0] + caps[1]).clean()
    pin.label = "through_pin_with_caps"
    return moving_fin, fixed_parts, fixed_feet, fixed_knuckles, shaft, caps, pin


def same_geometry(a, b, tol=0.02):
    sa, sb = signature(a), signature(b)
    if len(sa) != len(sb):
        return False
    for left, right in zip(sa, sb):
        if abs(left[0] - right[0]) > max(tol, abs(left[0]) * 1.0e-7):
            return False
        if any(abs(x - y) > tol for x, y in zip(left[1] + left[2], right[1] + right[2])):
            return False
    return True


def check_single_valid(shape):
    items = solids(shape)
    errors = topology_errors(shape)
    return {
        "solid_count": len(items),
        "positive_volumes_mm3": [float(item.volume) for item in items],
        "topology_error_count": len(errors),
        "topology_error_codes": [str(issue.code) for issue in errors],
        "pass": len(items) == 1 and all(item.volume > 0 for item in items) and not errors,
    }


def min_clearance(moving, obstacles):
    minimum = math.inf
    witness = None
    tested = 0
    colliding = []
    candidates = []
    for obstacle_name, obstacle in obstacles:
        for moving_solid in solids(moving):
            for obstacle_solid in solids(obstacle):
                candidates.append((bbox_gap(moving_solid, obstacle_solid), obstacle_name, moving_solid, obstacle_solid))
    candidates.sort(key=lambda item: item[0])
    smallest_skipped_bound = None
    for lower_bound, obstacle_name, moving_solid, obstacle_solid in candidates:
        # AABB distance is a conservative lower bound. Once it exceeds the best exact
        # distance, later pairs cannot reduce the reported global minimum.
        if lower_bound > minimum:
            smallest_skipped_bound = lower_bound
            break
        tested += 1
        overlap = float(overlap_volume(moving_solid, obstacle_solid))
        if overlap > OVERLAP_EPS_MM3:
            colliding.append({"obstacle": obstacle_name, "overlap_mm3": overlap})
            minimum = 0.0
            witness = obstacle_name
            continue
        result = closest_points(moving_solid, obstacle_solid)
        distance = float(result.distance)
        if distance < minimum:
            minimum = distance
            witness = obstacle_name
    if minimum is math.inf:
        minimum = None
    return {
        "minimum_clearance_mm": minimum,
        "witness_obstacle": witness,
        "exact_pairs_tested": tested,
        "smallest_skipped_AABB_lower_bound_mm": smallest_skipped_bound,
        "collisions": colliding,
        "pass": not colliding and minimum is not None and minimum > MIN_CLEARANCE,
    }


def main():
    report = {
        "gate": "rear_fin_R1_one_corner_feasibility",
        "units": "mm",
        "inputs": {},
        "geometry": {},
        "checks": {},
        "blockers": [],
    }
    for path in (BODY_STEP, ASSEMBLY_STEP):
        if not path.is_file():
            raise FileNotFoundError(f"Required immutable saved A5 input missing: {path}")
        report["inputs"][path.name] = {
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    body_shape = read_step(str(BODY_STEP))
    assembly_scene = read_scene(str(ASSEMBLY_STEP))
    assembly_leaves = []
    for occurrence in assembly_scene.leaves():
        occurrence_shape = occurrence.shape()
        assembly_leaves.append((str(occurrence.label), occurrence_shape))
    body_matches = [
        (label, shape)
        for label, shape in assembly_leaves
        if same_geometry(shape, body_shape)
    ]
    report["inputs"]["assembly_occurrences"] = [
        {"label": label, **describe_shape(shape)} for label, shape in assembly_leaves
    ]
    if len(body_matches) != 1:
        raise RuntimeError(
            "Could not identify exactly one unchanged saved-body occurrence in the A5 stowed assembly; "
            f"body STEP signature matched {len(body_matches)} occurrences"
        )
    body_label, matched_body = body_matches[0]
    report["inputs"]["identified_body_occurrence"] = body_label
    assembly_obstacles = [
        (label, shape) for label, shape in assembly_leaves if label != body_label
    ]
    # Full obstacle list uses the exact stowed A5 assembly, including its body.
    full_obstacles = [(f"A5:{label}", shape) for label, shape in assembly_leaves]

    moving, fixed_parts, feet, knuckles, shaft, caps, pin = build_geometry()
    report["geometry"]["dimensions"] = {
        "panel_planform_X_v": PANEL_PLANFORM,
        "panel_mapping": "Y=82-v; Z=87..90",
        "root_tube_X": ROOT_X,
        "root_tube_outer_radius_mm": 3.0,
        "moving_bore_radius_mm": BORE_RADIUS,
        "fixed_knuckle_X": FIXED_X,
        "fixed_knuckle_outer_radius_mm": 3.0,
        "fixed_bore_radius_mm": BORE_RADIUS,
        "foot_YZ": [79.0, 84.5, 80.0, 88.5],
        "pin_shaft_X": PIN_SHAFT_X,
        "pin_radius_mm": PIN_RADIUS,
        "cap_X": CAP_X,
        "cap_radius_mm": CAP_RADIUS,
        "fold_angle_deg": FOLD_ANGLE_DEG,
        "foot_X_used": FIXED_X,
    }
    all_new_parts = [moving, *fixed_parts, pin]
    report["geometry"]["parts"] = {
        shape.label: describe_shape(shape) for shape in all_new_parts
    }
    report["checks"]["single_solid_topology"] = {
        shape.label: check_single_valid(shape) for shape in all_new_parts
    }

    # Axis, bore, fit, and stowed-radius checks are analytic from construction plus BREP bounds.
    moving_bb = bbox_data(moving)
    fixed_bbs = [bbox_data(part) for part in fixed_parts]
    pin_bb = bbox_data(pin)
    fit_bbs = [moving_bb, *fixed_bbs, pin_bb]
    x_min = min(bb["min"][0] for bb in fit_bbs)
    x_max = max(bb["max"][0] for bb in fit_bbs)
    stowed_radii = {shape.label: radial_bound(shape) for shape in all_new_parts}
    report["checks"]["datums_and_envelopes"] = {
        "hinge_axis_direction": [1.0, 0.0, 0.0],
        "hinge_axis_point_YZ": [HINGE_Y, HINGE_Z],
        "all_new_parts_X_envelope_mm": [x_min, x_max],
        "required_X_envelope_mm": list(X_LIMITS),
        "stowed_conservative_radial_bounds_mm": stowed_radii,
        "stowed_radial_limit_mm_exclusive": 125.0,
        "pass": x_min >= X_LIMITS[0] and x_max <= X_LIMITS[1] and all(r < 125.0 for r in stowed_radii.values()),
    }
    axis_line = bd.Edge.make_line((ROOT_X[0], HINGE_Y, HINGE_Z), (ROOT_X[1], HINGE_Y, HINGE_Z))
    # Construction-axis residuals are reported as exact coordinate offsets; STEP bodies stay untouched.
    report["checks"]["axis_and_bores"] = {
        "axis_line_length_mm": float(axis_line.length),
        "moving_bore_radius_mm": BORE_RADIUS,
        "fixed_bore_radii_mm": [BORE_RADIUS, BORE_RADIUS],
        "shaft_radius_mm": PIN_RADIUS,
        "radial_clearance_mm": BORE_RADIUS - PIN_RADIUS,
        "cap_radii_mm": [CAP_RADIUS, CAP_RADIUS],
        "cap_to_knuckle_axial_gaps_mm": [
            FIXED_X[0][0] - CAP_X[0][1],
            CAP_X[1][0] - FIXED_X[1][1],
        ],
        "panel_to_knuckle_axial_gaps_mm": [
            ROOT_X[0] - FIXED_X[0][1],
            FIXED_X[1][0] - ROOT_X[1],
        ],
        "pass": (
            abs((BORE_RADIUS - PIN_RADIUS) - 0.25) < 1.0e-9
            and CAP_RADIUS <= 2.5
            and abs((FIXED_X[0][0] - CAP_X[0][1]) - 0.3) < 1.0e-9
            and abs((CAP_X[1][0] - FIXED_X[1][1]) - 0.3) < 1.0e-9
            and abs((ROOT_X[0] - FIXED_X[0][1]) - 1.0) < 1.0e-9
            and abs((FIXED_X[1][0] - ROOT_X[1]) - 1.0) < 1.0e-9
        ),
    }

    # Only foot/body overlap is intentional; the separate cut knuckle sub-shape must not overlap body.
    contact_results = []
    for index, (foot, knuckle, fixed) in enumerate(zip(feet, knuckles, fixed_parts), start=1):
        foot_overlap = float(overlap_volume(solids(foot)[0], solids(body_shape)[0]))
        knuckle_overlap = float(overlap_volume(solids(knuckle)[0], solids(body_shape)[0]))
        full_overlap = float(overlap_volume(solids(fixed)[0], solids(body_shape)[0]))
        contact_results.append({
            "pair": [f"fixed_knuckle_foot_{index}", "A5_body"],
            "foot_body_overlap_mm3": foot_overlap,
            "knuckle_body_overlap_mm3": knuckle_overlap,
            "combined_fixed_part_body_overlap_mm3": full_overlap,
            "intentional_pair": True,
            "pass": foot_overlap > CONTACT_EPS_MM3 and knuckle_overlap <= OVERLAP_EPS_MM3,
        })
    report["checks"]["intentional_foot_contacts"] = {
        "only_allowed_pairs": [["fixed_knuckle_foot_1", "A5_body"], ["fixed_knuckle_foot_2", "A5_body"]],
        "contacts": contact_results,
        "pass": all(item["pass"] for item in contact_results),
    }

    # Fixed hardware and pin must clear all saved A5 components; only foot/body support is exempted.
    fixed_collisions = []
    fixed_clearances = []
    for part in [*fixed_parts, pin]:
        clear = min_clearance(part, full_obstacles)
        fixed_clearances.append({"part": part.label, **clear})
        for collision in clear["collisions"]:
            # The checker treats the whole fused support's body interference separately above.
            if collision["obstacle"] == f"A5:{body_label}" and part in fixed_parts:
                continue
            fixed_collisions.append({"part": part.label, **collision})
    report["checks"]["fixed_hardware_vs_A5"] = {
        "clearances": fixed_clearances,
        "nonintentional_collisions": fixed_collisions,
        "pass": not fixed_collisions and all(
            item["pass"] or (item["part"].startswith("fixed_knuckle_foot_") and item["witness_obstacle"] == f"A5:{body_label}")
            for item in fixed_clearances
        ),
    }

    # Moving fin and root are sampled at exactly 31 equally spaced fold fractions.
    motion = []
    axis = bd.Axis((0.0, HINGE_Y, HINGE_Z), (1.0, 0.0, 0.0))
    for sample_index in range(SAMPLES):
        fraction = sample_index / (SAMPLES - 1)
        posed = moving.rotate(axis, FOLD_ANGLE_DEG * fraction)
        clear = min_clearance(posed, full_obstacles)
        motion.append({
            "sample": sample_index,
            "fraction": fraction,
            "angle_deg": FOLD_ANGLE_DEG * fraction,
            **clear,
        })
    motion_collisions = [
        {"sample": item["sample"], "fraction": item["fraction"], "collision": collision}
        for item in motion for collision in item["collisions"]
    ]
    moving_clearances = [item["minimum_clearance_mm"] for item in motion if item["minimum_clearance_mm"] is not None]
    report["checks"]["fold_motion_vs_A5"] = {
        "sample_count": len(motion),
        "samples": motion,
        "minimum_sampled_clearance_mm": min(moving_clearances) if moving_clearances else None,
        "collision_count": len(motion_collisions),
        "collisions": motion_collisions,
        "required_clearance_mm_exclusive": MIN_CLEARANCE,
        "pass": len(motion) == SAMPLES and not motion_collisions and bool(moving_clearances) and min(moving_clearances) > MIN_CLEARANCE,
    }

    # Check pin-to-bore fit as actual BREP distances, not only nominal radii.
    pin_fit = []
    for part in [moving, *fixed_parts]:
        distance = float(closest_points(solids(pin)[0], solids(part)[0]).distance)
        overlap = float(overlap_volume(solids(pin)[0], solids(part)[0]))
        pin_fit.append({
            "pair": [pin.label, part.label],
            "surface_clearance_mm": distance,
            "overlap_mm3": overlap,
            "pass": overlap <= OVERLAP_EPS_MM3 and distance >= 0.25 - 1.0e-5,
        })
    report["checks"]["pin_fit"] = {
        "pairs": pin_fit,
        "pass": all(item["pass"] for item in pin_fit),
    }

    # Preserve detailed evidence but expose an overall feasibility verdict and exact blockers.
    checks = report["checks"]
    for name, result in checks["single_solid_topology"].items():
        if not result["pass"]:
            report["blockers"].append(f"{name} is not one positive-volume topologically valid solid")
    for name in ("datums_and_envelopes", "axis_and_bores", "intentional_foot_contacts", "fixed_hardware_vs_A5", "fold_motion_vs_A5", "pin_fit"):
        if not checks[name]["pass"]:
            report["blockers"].append(f"{name} failed; see measured details in checks.{name}")
    report["feasible"] = not report["blockers"]
    report["summary"] = (
        "All one-corner feasibility checks passed; geometry remains a rough, unselected trial."
        if report["feasible"]
        else "One-corner feasibility is blocked; no repeated fins or A5 source changes were made."
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT),
        "feasible": report["feasible"],
        "blockers": report["blockers"],
        "single_solid_topology": {k: v["pass"] for k, v in checks["single_solid_topology"].items()},
        "stowed_bounds_mm": checks["datums_and_envelopes"]["stowed_conservative_radial_bounds_mm"],
        "foot_contacts": checks["intentional_foot_contacts"]["contacts"],
        "fixed_hardware_pass": checks["fixed_hardware_vs_A5"]["pass"],
        "motion_samples": len(motion),
        "motion_min_clearance_mm": checks["fold_motion_vs_A5"]["minimum_sampled_clearance_mm"],
        "motion_collision_count": len(motion_collisions),
        "pin_fit": checks["pin_fit"]["pairs"],
    }, indent=2))
    if not report["feasible"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
