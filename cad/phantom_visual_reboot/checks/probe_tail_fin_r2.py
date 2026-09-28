"""R2 aft-shift feasibility probe using saved R1 STEP parts and immutable A5."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import build123d as bd
from cadgen.geometry import closest_points, overlap_volume


ROOT = Path(__file__).resolve().parents[1]
SAVED_TAIL = ROOT / "STEP" / "Q_Tail_R1_Tall_Stowed.step"
SAVED_A5 = ROOT / "STEP" / "O_Interleaved_A5_Stowed.step"
REPORT = ROOT / "reviews" / "tail_fin_r2_probe.json"
TAIL_LABELS = (
    "tail_r1_fin_root",
    "tail_r1_fixed_knuckle_aft",
    "tail_r1_fixed_knuckle_forward",
    "tail_r1_throughpin",
)
SUPPORT_LABELS = TAIL_LABELS[1:3]
BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
SHIFT_X = -80.0
HINGE_Y = 82.0
HINGE_Z = 88.5
FOLD_ANGLE_DEG = -135.0
FOLD_SAMPLES = tuple(i / 30.0 for i in range(31))
CLEARANCE_MM = 0.2
OVERLAP_TOL_MM3 = 0.001
CONTACT_EPS_MM3 = 1.0e-5
RADIAL_LIMIT_MM = 125.0
X_LIMITS_MM = (-1400.0, 1400.0)


def parts_from_step(path: Path):
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


def exact_minimum(pairs):
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
        amount = float(overlap_volume(a, b))
        exact_count += 1
        distance = 0.0 if amount > OVERLAP_TOL_MM3 else float(closest_points(a, b).distance)
        if amount > OVERLAP_TOL_MM3:
            overlaps.append({"pair": name, "overlap_mm3": amount})
        if distance < best:
            best, witness = distance, name
    return {
        "minimum_clearance_mm": None if math.isinf(best) else best,
        "witness_pair": witness,
        "exact_pairs_tested": exact_count,
        "AABB_lower_bound_pairs_pruned": skipped,
        "overlaps_over_0_001_mm3": overlaps,
    }


def closest_point_evidence(a, b):
    result = closest_points(a, b)
    evidence = {"distance_mm": float(result.distance)}
    for name in ("point_a", "point_b", "point1", "point2", "p1", "p2", "first", "second"):
        value = getattr(result, name, None)
        if value is not None:
            try:
                evidence[name] = [float(value.X), float(value.Y), float(value.Z)]
            except Exception:
                evidence[name] = str(value)
    return evidence


def solid_metrics(shape):
    solids = list(shape.solids())
    volumes = [float(s.volume) for s in solids]
    return {
        "solid_count": len(solids),
        "positive_volumes_mm3": volumes,
        "valid": bool(shape.is_valid),
        "pass": bool(shape.is_valid and len(solids) == 1 and volumes and all(v > 0 for v in volumes)),
    }


def main():
    report = {
        "gate": "rear_fin_R2_aft_shift_feasibility",
        "units": "mm",
        "transform": {"all_four_saved_tail_parts_translation_mm": [SHIFT_X, 0.0, 0.0]},
        "thresholds": {
            "stowed_conservative_radius_mm_exclusive": RADIAL_LIMIT_MM,
            "tail_X_limits_mm_inclusive": list(X_LIMITS_MM),
            "clearance_mm_exclusive": CLEARANCE_MM,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "fold_sample_count": len(FOLD_SAMPLES),
            "fold_angle_deg": FOLD_ANGLE_DEG,
        },
        "inputs": {},
        "checks": {},
        "failures": [],
    }
    for path in (SAVED_TAIL, SAVED_A5):
        if not path.is_file():
            raise FileNotFoundError(f"Required immutable saved STEP missing: {path}")
        report["inputs"][path.name] = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    tail_saved, tail_duplicates = parts_from_step(SAVED_TAIL)
    a5, a5_duplicates = parts_from_step(SAVED_A5)
    missing_tail = sorted(set(TAIL_LABELS) - set(tail_saved))
    if tail_duplicates or missing_tail:
        raise RuntimeError(f"Saved tall STEP inventory invalid: duplicates={tail_duplicates}, missing={missing_tail}")
    if a5_duplicates or BODY_LABEL not in a5:
        raise RuntimeError(f"Saved A5 inventory invalid: duplicates={a5_duplicates}, body_present={BODY_LABEL in a5}")
    report["inputs"]["saved_tail_inventory"] = sorted(tail_saved)
    report["inputs"]["saved_A5_inventory"] = sorted(a5)

    tail = {label: tail_saved[label].translate((SHIFT_X, 0.0, 0.0)) for label in TAIL_LABELS}
    body = a5[BODY_LABEL]
    sys.path.insert(0, str(ROOT / "src"))
    import check_interleaved_a5 as a5check

    stowed_base = a5
    canonical_panels = {}
    for label in a5check.PANELS:
        if label in stowed_base:
            side, kind = label.split("_")
            canonical_panels[label] = a5check.panel_canonical(
                stowed_base[label], side, kind, a5check.CUMULATIVE_A2_DROP_MM
            )
    required_moving = (*a5check.PANELS, *a5check.SUPPORTS)
    if any(label not in stowed_base for label in required_moving):
        absent = [label for label in required_moving if label not in stowed_base]
        raise RuntimeError(f"Saved A5 base lacks required reconstructed moving parts: {absent}")

    topology = {label: solid_metrics(tail[label]) for label in TAIL_LABELS}
    report["checks"]["saved_translated_part_topology"] = topology
    for label, result in topology.items():
        if not result["pass"]:
            report["failures"].append({"check": "translated_saved_part_topology", "label": label, "metrics": result})
    a5_topology = {label: solid_metrics(shape) for label, shape in a5.items()}
    report["checks"]["immutable_saved_A5_topology"] = a5_topology
    for label, result in a5_topology.items():
        if not result["pass"]:
            report["failures"].append({"check": "immutable_saved_A5_topology", "label": label, "metrics": result})

    envelopes = {}
    for label, shape in tail.items():
        lo, hi = bbox(shape)
        envelopes[label] = {
            "X_mm": [lo[0], hi[0]],
            "conservative_YZ_radius_mm": radial_bound(shape),
            "within_X_limits": lo[0] >= X_LIMITS_MM[0] and hi[0] <= X_LIMITS_MM[1],
            "within_stowed_radius": radial_bound(shape) < RADIAL_LIMIT_MM,
        }
    report["checks"]["translated_envelopes"] = {
        "parts": envelopes,
        "moving_root_X_mm": envelopes[TAIL_LABELS[0]]["X_mm"],
        "fixed_pin_span_X_mm": envelopes[TAIL_LABELS[3]]["X_mm"],
        "pass": all(v["within_X_limits"] and v["within_stowed_radius"] for v in envelopes.values()),
    }
    if not report["checks"]["translated_envelopes"]["pass"]:
        report["failures"].append({"check": "translated_envelopes"})

    # Isolate the foot solids from saved fused support STEP shapes, then classify
    # support solely by measured foot/body overlap; knuckle/body remains forbidden.
    foot_ranges = ((-1335.0, -1326.0), (-1084.0, -1075.0))
    feet = {}
    knuckles = {}
    contacts = []
    for label, (x0, x1) in zip(SUPPORT_LABELS, foot_ranges):
        foot_box = bd.Solid.make_box(x1 - x0, 5.5, 8.5,
                                     plane=bd.Plane(origin=(x0, 79.0, 80.0)))
        foot = (tail[label] & foot_box).clean()
        knuckle = (tail[label] - foot_box).clean()
        feet[label], knuckles[label] = foot, knuckle
        foot_overlap = float(overlap_volume(foot, body))
        knuckle_overlap = float(overlap_volume(knuckle, body))
        total_overlap = float(overlap_volume(tail[label], body))
        foot_gap = closest_point_evidence(foot, body) if foot_overlap <= CONTACT_EPS_MM3 else None
        row = {
            "support": label,
            "foot_X_mm": [x0, x1],
            "foot_body_overlap_mm3": foot_overlap,
            "isolated_knuckle_body_overlap_mm3": knuckle_overlap,
            "combined_support_body_overlap_mm3": total_overlap,
            "foot_body_closest_points_if_unseated": foot_gap,
            "pass": foot_overlap > CONTACT_EPS_MM3 and knuckle_overlap < OVERLAP_TOL_MM3
                     and abs(total_overlap - foot_overlap) < 0.01,
        }
        contacts.append(row)
        if not row["pass"]:
            report["failures"].append({"check": "fixed_foot_body_contact_and_knuckle_clearance", **row})
    report["checks"]["fixed_foot_body_contacts"] = {
        "only_allowed_pairs": [[label, BODY_LABEL] for label in SUPPORT_LABELS],
        "supports": contacts,
        "pass": all(row["pass"] for row in contacts),
    }

    # Stationary hardware and the pin must clear every saved A5 part; only the
    # actual support/body attachment is excluded from this clearance inventory.
    base_labels = sorted(a5)
    static_hardware = {}
    for label in (*SUPPORT_LABELS, TAIL_LABELS[3]):
        obstacles = [(f"A5:{name}", part) for name, part in a5.items()
                     if not (label in SUPPORT_LABELS and name == BODY_LABEL)]
        result = exact_minimum([(name, tail[label], obstacle) for name, obstacle in obstacles])
        result["pass"] = (result["minimum_clearance_mm"] is not None
                          and result["minimum_clearance_mm"] > CLEARANCE_MM
                          and not result["overlaps_over_0_001_mm3"])
        static_hardware[label] = result
        if not result["pass"]:
            report["failures"].append({"check": "translated_fixed_hardware_A5_clearance", "label": label, **result})
    report["checks"]["fixed_hardware_vs_saved_A5"] = {
        "clearances": static_hardware,
        "pass": all(row["pass"] for row in static_hardware.values()),
    }

    # Saved pin fit and stowed tail-part pair clearances/overlaps after translation.
    pin = tail[TAIL_LABELS[3]]
    pin_fit = []
    for label in TAIL_LABELS[:3]:
        overlap = float(overlap_volume(pin, tail[label]))
        distance = float(closest_points(pin, tail[label]).distance)
        pin_fit.append({"pair": [TAIL_LABELS[3], label], "overlap_mm3": overlap,
                        "surface_clearance_mm": distance,
                        "pass": overlap < OVERLAP_TOL_MM3 and abs(distance - 0.25) < 1.0e-4})
    report["checks"]["saved_pin_fit_unchanged"] = {"pairs": pin_fit, "pass": all(row["pass"] for row in pin_fit)}
    if not report["checks"]["saved_pin_fit_unchanged"]["pass"]:
        report["failures"].append({"check": "saved_pin_fit_unchanged"})

    tail_pair_overlaps = []
    for index, first in enumerate(TAIL_LABELS):
        for second in TAIL_LABELS[index + 1:]:
            if bbox_gap(tail[first], tail[second]) > 0:
                continue
            amount = float(overlap_volume(tail[first], tail[second]))
            if amount >= OVERLAP_TOL_MM3:
                tail_pair_overlaps.append({"pair": [first, second], "overlap_mm3": amount})
    report["checks"]["stowed_tail_mutual_overlaps"] = {
        "unexpected_overlaps_ge_0_001_mm3": tail_pair_overlaps,
        "pass": not tail_pair_overlaps,
    }
    if tail_pair_overlaps:
        report["failures"].append({"check": "stowed_tail_mutual_overlaps", "overlaps": tail_pair_overlaps})

    motion_rows = []
    hardware_rows = []
    for sample_index, fraction in enumerate(FOLD_SAMPLES):
        a5_pose = a5check.move_saved_stowed(
            stowed_base, fraction, canonical_panels, a5check.CUMULATIVE_A2_DROP_MM
        )
        moving_fin = tail[TAIL_LABELS[0]].rotate(
            bd.Axis((0.0, HINGE_Y, HINGE_Z), (1.0, 0.0, 0.0)), FOLD_ANGLE_DEG * fraction
        )
        obstacles = [(f"tail:{label}", tail[label]) for label in TAIL_LABELS[1:]]
        obstacles.extend((f"A5:{label}", a5_pose[label]) for label in base_labels)
        result = exact_minimum([(name, moving_fin, obstacle) for name, obstacle in obstacles])
        result.update({"sample": sample_index, "fraction": fraction,
                       "angle_deg": FOLD_ANGLE_DEG * fraction,
                       "obstacle_pair_count": len(obstacles)})
        result["pass"] = (result["minimum_clearance_mm"] is not None
                          and result["minimum_clearance_mm"] > CLEARANCE_MM
                          and not result["overlaps_over_0_001_mm3"])
        motion_rows.append(result)

        per_hardware = {}
        for label in (*SUPPORT_LABELS, TAIL_LABELS[3]):
            pairs = [(f"A5:{name}", tail[label], a5_pose[name]) for name in base_labels
                     if not (label in SUPPORT_LABELS and name == BODY_LABEL)]
            hardware_result = exact_minimum(pairs)
            hardware_result["pass"] = (hardware_result["minimum_clearance_mm"] is not None
                                        and hardware_result["minimum_clearance_mm"] > CLEARANCE_MM
                                        and not hardware_result["overlaps_over_0_001_mm3"])
            per_hardware[label] = hardware_result
        hardware_rows.append({"sample": sample_index, "fraction": fraction,
                              "parts": per_hardware,
                              "pass": all(row["pass"] for row in per_hardware.values())})

    motion_values = [row["minimum_clearance_mm"] for row in motion_rows
                     if row["minimum_clearance_mm"] is not None]
    hardware_minima = [result["minimum_clearance_mm"]
                       for sample in hardware_rows for result in sample["parts"].values()
                       if result["minimum_clearance_mm"] is not None]
    report["checks"]["fold_motion_vs_tail_hardware_and_A5"] = {
        "sample_count": len(motion_rows),
        "samples": motion_rows,
        "minimum_sampled_clearance_mm": min(motion_values) if motion_values else None,
        "minimum_witness": min(motion_rows, key=lambda r: r["minimum_clearance_mm"]
                                if r["minimum_clearance_mm"] is not None else math.inf).get("witness_pair"),
        "collision_count": sum(len(row["overlaps_over_0_001_mm3"]) for row in motion_rows),
        "pass": len(motion_rows) == 31 and all(row["pass"] for row in motion_rows),
    }
    report["checks"]["stationary_hardware_vs_A5_motion"] = {
        "sample_count": len(hardware_rows),
        "samples": hardware_rows,
        "minimum_sampled_clearance_mm": min(hardware_minima) if hardware_minima else None,
        "pass": len(hardware_rows) == 31 and all(row["pass"] for row in hardware_rows),
    }
    if not report["checks"]["fold_motion_vs_tail_hardware_and_A5"]["pass"]:
        report["failures"].append({"check": "fold_motion_vs_tail_hardware_and_A5"})
    if not report["checks"]["stationary_hardware_vs_A5_motion"]["pass"]:
        report["failures"].append({"check": "stationary_hardware_vs_A5_motion"})

    report["passed"] = not report["failures"]
    report["summary"] = {
        "passed": report["passed"],
        "failure_count": len(report["failures"]),
        "translated_moving_root_X_mm": envelopes[TAIL_LABELS[0]]["X_mm"],
        "translated_pin_span_X_mm": envelopes[TAIL_LABELS[3]]["X_mm"],
        "maximum_stowed_radius_mm": max(v["conservative_YZ_radius_mm"] for v in envelopes.values()),
        "foot_body_overlap_mm3": {row["support"]: row["foot_body_overlap_mm3"] for row in contacts},
        "knuckle_body_overlap_mm3": {row["support"]: row["isolated_knuckle_body_overlap_mm3"] for row in contacts},
        "motion_samples": len(motion_rows),
        "motion_min_clearance_mm": report["checks"]["fold_motion_vs_tail_hardware_and_A5"]["minimum_sampled_clearance_mm"],
        "stationary_hardware_min_clearance_mm": report["checks"]["stationary_hardware_vs_A5_motion"]["minimum_sampled_clearance_mm"],
        "pin_fit_clearances_mm": {row["pair"][1]: row["surface_clearance_mm"] for row in pin_fit},
    }
    report["blockers"] = report["failures"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), **report["summary"], "blockers": report["blockers"]}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
