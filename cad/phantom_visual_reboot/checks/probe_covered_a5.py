"""Bounded in-memory feasibility probe for the covered A5 body recess.

Reads the saved A4 STEP parts and the approved A/A2/A4 source motion law. It
does not modify model sources or build/export production artifacts.
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

import interleaved_wing_a4 as a4  # noqa: E402
from interleaved_wing_a2 import body as a2_body  # noqa: E402
from interleaved_wing_a import pose as pose_a  # noqa: E402
from joined_wing_r1 import (FRONT_LENGTH, OPEN_SEPARATION, REAR_LENGTH,
                            STOW_SEPARATION)  # noqa: E402

OUT = ROOT / "reviews/covered_a5_probe.json"
A4_STOWED = ROOT / "STEP/O_Interleaved_A4_Stowed.step"
A4_MODULE = ROOT / "STEP/O_Interleaved_A4_Module_Stowed.step"
BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
DROP_A5 = 5.5
CLEARANCE = 0.3
PIN_RADIUS = 3.5
CAP_RADIUS = 7.0
EARLY_FRACTIONS = (0.0, 0.0001, 0.00025, 0.0005, 0.001, 0.002, 0.003,
                   0.005, 0.01, 0.02, 0.05)
FRACTIONS = sorted(set(EARLY_FRACTIONS) | {i / 20 for i in range(21)})
WELL = (-450.3, 550.3, -74.3, 74.3, 57.75, 84.0)
SLOTS_A4 = (
    (-430.0, 530.0, 0.0, 100.0, 65.7, 70.3),
    (-430.0, 530.0, 0.0, 100.0, 76.2, 80.8),
    (-430.0, 530.0, -100.0, 0.0, 71.2, 75.8),
    (-430.0, 530.0, -100.0, 0.0, 81.7, 86.3),
)
COVER = (-455.0, 555.0, -76.0, 76.0, 84.0, 86.0)
COVER_SEAT = (-455.0, 555.0, -76.0, 76.0, 84.0, 100.0)
CONTACT_TOL = 0.001
OVERLAP_TOL = 0.001


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


def box(ext):
    x0, x1, y0, y1, z0, z1 = ext
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def bounds(shape):
    b = shape.bounding_box()
    return {"x": [float(b.min.X), float(b.max.X)],
            "y": [float(b.min.Y), float(b.max.Y)],
            "z": [float(b.min.Z), float(b.max.Z)]}


def solid_ok(shape):
    return bool(shape.is_valid and len(shape.solids()) == 1 and volume(shape) > 0)


def parts_from_step(path):
    shape = bd.import_step(path)
    result = {}
    for part in (list(shape.children) or [shape]):
        result[str(part.label)] = part
    return result


def cylinder(radius, z0, z1, xy):
    return bd.Cylinder(radius, z1 - z0,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
                       ).translate((xy[0], xy[1], z0))


def annular_sector(cx, cy, radius, z0, z1, theta0, theta1):
    """True revolved radial/Z profile, covering the complete angular interval."""
    inner, outer = 900.0 - radius, 900.0 + radius
    t = math.radians(theta0)
    points = [(cx + inner * math.cos(t), cy + inner * math.sin(t), z0),
              (cx + outer * math.cos(t), cy + outer * math.sin(t), z0),
              (cx + outer * math.cos(t), cy + outer * math.sin(t), z1),
              (cx + inner * math.cos(t), cy + inner * math.sin(t), z1)]
    face = bd.Face(bd.Wire.make_polygon(points, close=True))
    return bd.revolve(face, axis=bd.Axis((cx, cy, 0), (0, 0, 1)),
                      revolution_arc=theta1 - theta0).clean()


def step_solid_intersection(a, b):
    return volume(a & b)


def main():
    report = {
        "gate": "A5 covered recess feasibility only; no production build",
        "inputs": {"A4_stowed_step": str(A4_STOWED),
                   "A4_module_stowed_step": str(A4_MODULE),
                   "nonbody_shift_mm": [0.0, 0.0, -DROP_A5],
                   "cumulative_A2_shift_mm": 28.25},
        "spec_mm": {"well": list(WELL), "cover": list(COVER),
                    "cover_seat_cut": list(COVER_SEAT), "cover_thickness": 2.0,
                    "slot_z_shift_mm": -DROP_A5,
                    "pin_radial_clearance_mm": CLEARANCE,
                    "pin_axial_clearance_mm": CLEARANCE},
        "saved_A4_join_ranges": {}, "full_law_arc": {},
        "original_A4_early_motion": [], "candidate_body": {},
        "candidate_cover": {}, "candidate_motion_clearance": {},
        "failures": [],
    }
    try:
        saved_full = parts_from_step(A4_STOWED)
        saved_module = parts_from_step(A4_MODULE)
        report["saved_A4_part_inventory"] = {
            "full_labels": sorted(saved_full), "module_labels": sorted(saved_module),
            "part_counts": [len(saved_full), len(saved_module)]}
        if BODY_LABEL not in saved_full:
            raise RuntimeError("A4 saved full STEP is missing the body label")
        original_body = saved_full[BODY_LABEL]

        # Extract the cap's outer radial shell from each saved A4 join pin. Its
        # Z bounding planes are the saved cap planes; the remainder gives shaft.
        saved_ranges = {}
        pin_centres = {}
        for side in ("starboard", "port"):
            label = side + "_join"
            pin = saved_module[label]
            p = pose_a(0.0, side)["joint"]
            centre = (float(p[0]), float(p[1]))
            pin_centres[side] = centre
            zpin = bounds(pin)["z"]
            shell = cylinder(6.9, zpin[0] - 2, zpin[1] + 2, centre) - cylinder(
                3.6, zpin[0] - 2, zpin[1] + 2, centre)
            cap_shell = pin & shell
            cap_bounds = bounds(cap_shell)["z"]
            shaft = [zpin[0], cap_bounds[0]]
            cap = cap_bounds
            saved_ranges[side] = {
                "label": label, "saved_pin_bounds_z_mm": zpin,
                "saved_shaft_z_mm": shaft, "saved_cap_z_mm": cap,
                "trial_shaft_z_mm": [shaft[0] - DROP_A5, shaft[1] - DROP_A5],
                "trial_cap_z_mm": [cap[0] - DROP_A5, cap[1] - DROP_A5],
                "axis_xy_mm": list(centre),
            }
        report["saved_A4_join_ranges"] = saved_ranges

        # Establish endpoint angles and radial-law consistency from the actual
        # approved A pose function; the circles are then sector-swept continuously.
        arc_info = {}
        sector_bounds = {}
        critical_separation = math.sqrt(FRONT_LENGTH ** 2 - REAR_LENGTH ** 2)
        critical_fraction = ((critical_separation - STOW_SEPARATION) /
                             (OPEN_SEPARATION - STOW_SEPARATION))
        for side, cy in (("starboard", 30.0), ("port", -30.0)):
            p0, p1 = pose_a(0.0, side), pose_a(1.0, side)
            pc = pose_a(critical_fraction, side)
            centre = (500.0, cy)
            angles = []
            radii = []
            angle_track = []
            for i in range(1001):
                p = pose_a(i / 1000, side)["joint"]
                dx, dy = p[0] - centre[0], p[1] - centre[1]
                radii.append(math.hypot(dx, dy))
                angle_track.append(math.degrees(math.atan2(dy, dx)))
            angle0 = math.degrees(math.atan2(p0["joint"][1] - cy,
                                              p0["joint"][0] - 500.0))
            anglec = math.degrees(math.atan2(pc["joint"][1] - cy,
                                              pc["joint"][0] - 500.0))
            angle1 = math.degrees(math.atan2(p1["joint"][1] - cy,
                                              p1["joint"][0] - 500.0))
            # The line-link law is not monotonic in angle: with separation s,
            # the axial leg a=(L^2-R^2+s^2)/(2s) has its interior minimum at
            # s=sqrt(L^2-R^2). Evaluate that analytic stationary pose as well
            # as both endpoints so the sector includes the complete arc.
            lo, hi = min(angle0, anglec, angle1), max(angle0, anglec, angle1)
            sampled_interval_covered = (min(angle_track) >= lo - 1e-9 and
                                        max(angle_track) <= hi + 1e-9)
            arc_info[side] = {
                "centre_xy_mm": list(centre), "radius_target_mm": 900.0,
                "endpoint_angles_deg": [angle0, angle1],
                "analytic_interior_extremum": {
                    "basis": "d((L^2-R^2+s^2)/(2s))/ds=0",
                    "separation_mm": critical_separation,
                    "fraction": critical_fraction,
                    "angle_deg": anglec,
                },
                "sector_angle_interval_deg": [lo, hi],
                "sampled_1001_min_radius_mm": min(radii),
                "sampled_1001_max_radius_mm": max(radii),
                "sampled_1001_max_radius_error_mm": max(abs(r - 900.0) for r in radii),
                "sampled_1001_angle_interval_deg": [min(angle_track), max(angle_track)],
                "analytic_extrema_bound_all_1001_angle_evaluations": sampled_interval_covered,
            }
            sector_bounds[side] = (lo, hi)
        report["full_law_arc"] = arc_info

        # Original A4: expose collisions missed by the regular 21 poses.
        original_collisions = []
        for fraction in FRACTIONS:
            parts = {str(p.label): p for p in a4.components(fraction)}
            entry = {"fraction": fraction, "join_pins": {}}
            for side in ("starboard", "port"):
                label = side + "_join"
                pin = parts[label]
                gap = float(original_body.distance_to(pin))
                overlap = step_solid_intersection(original_body, pin) if gap < CONTACT_TOL else 0.0
                entry["join_pins"][side] = {"body_gap_mm": gap,
                                             "body_overlap_mm3": overlap}
            original_collisions.append(entry)
        report["original_A4_early_motion"] = original_collisions
        report["original_A4_early_collision_summary"] = {
            "sample_fractions": FRACTIONS,
            "nonzero_join_pin_body_overlap_samples": [
                {"fraction": e["fraction"], "side": side,
                 "overlap_mm3": e["join_pins"][side]["body_overlap_mm3"]}
                for e in original_collisions for side in ("starboard", "port")
                if e["join_pins"][side]["body_overlap_mm3"] >= OVERLAP_TOL],
            "regular_21_fractions": [i / 20 for i in range(21)],
        }

        # Each shaft and cap gets a true full-angle annular sector plus endpoint
        # disks. Clip each cutter to the actual uncut A2 body before union/cut.
        body_source = a2_body()
        pin_tool_parts = []
        pin_tool_metrics = []
        for side, cy in (("starboard", 30.0), ("port", -30.0)):
            cx = 500.0
            lo, hi = sector_bounds[side]
            # Endpoint XY points follow the exact A4 full-motion pose law.
            endpoints = [pose_a(f, side)["joint"] for f in (0.0, 1.0)]
            for key, nominal_radius in (("shaft", PIN_RADIUS), ("cap", CAP_RADIUS)):
                zraw = saved_ranges[side]["saved_" + key + "_z_mm"]
                z0 = zraw[0] - DROP_A5 - CLEARANCE
                z1 = zraw[1] - DROP_A5 + CLEARANCE
                tool_radius = nominal_radius + CLEARANCE
                sector = annular_sector(cx, cy, tool_radius, z0, z1, lo, hi)
                disks = [cylinder(tool_radius, z0, z1, (float(p[0]), float(p[1])))
                         for p in endpoints]
                raw_tool = sector + disks[0] + disks[1]
                clipped = raw_tool & body_source
                pin_tool_parts.append(clipped)
                pin_tool_metrics.append({
                    "side": side, "feature": key, "nominal_radius_mm": nominal_radius,
                    "tool_radius_mm": tool_radius, "trial_z_with_clearance_mm": [z0, z1],
                    "sector_angle_interval_deg": [lo, hi],
                    "endpoint_discs": [{"xy_mm": [float(p[0]), float(p[1])],
                                         "radius_mm": tool_radius} for p in endpoints],
                    "analytic_tool_body_intersection_volume_mm3": volume(clipped),
                    "clipped_tool_valid": bool(clipped.is_valid and clipped.solids()),
                })
        panel_slots = []
        for x0, x1, y0, y1, z0, z1 in SLOTS_A4:
            panel_slots.append((x0, x1, y0, y1, z0 - DROP_A5, z1 - DROP_A5))
        fixed_cutters = [box(WELL)] + [box(s) for s in panel_slots]
        pin_union = pin_tool_parts[0]
        for tool in pin_tool_parts[1:]:
            pin_union = pin_union + tool
        all_cutters = fixed_cutters[0]
        for cutter in fixed_cutters[1:] + [pin_union, box(COVER_SEAT)]:
            all_cutters = all_cutters + cutter
        candidate_body = (body_source - all_cutters).clean()
        cover = box(COVER)
        body_cover_gap = float(candidate_body.distance_to(cover))
        body_cover_overlap = volume(candidate_body & cover) if body_cover_gap < CONTACT_TOL else 0.0
        landing_band = box((COVER[0], COVER[1], COVER[2], COVER[3], 83.99, 84.0))
        landing_band_volume = volume(candidate_body & landing_band)
        body_metrics = {
            "valid": bool(candidate_body.is_valid),
            "single_positive_solid": solid_ok(candidate_body),
            "solid_count": len(candidate_body.solids()),
            "volume_mm3": volume(candidate_body),
            "bounds_mm": bounds(candidate_body),
            "roof_top_z_mm": bounds(candidate_body)["z"][1],
            "cover_contact_gap_mm": body_cover_gap,
            "body_cover_overlap_mm3": body_cover_overlap,
            "cover_landing_band_volume_mm3_z83_99_to84": landing_band_volume,
            "cover_landing_area_proxy_mm2": landing_band_volume / 0.01,
            "cover_seat_area_bbox_mm2": (COVER_SEAT[1] - COVER_SEAT[0]) *
                                         (COVER_SEAT[3] - COVER_SEAT[2]),
            "pin_sweep_clipped_tool_metrics": pin_tool_metrics,
            "shifted_panel_slot_extents_mm": [list(s) for s in panel_slots],
        }
        report["candidate_body"] = body_metrics
        report["candidate_cover"] = {
            "valid_single_positive_solid": solid_ok(cover), "volume_mm3": volume(cover),
            "bounds_mm": bounds(cover), "body_gap_mm": body_cover_gap,
            "body_overlap_mm3": body_cover_overlap,
            "positive_ledge_support_evidence": landing_band_volume > 0,
            "assumption": "2 mm trial cover; feasibility geometry only, no structural proof",
        }

        # At 21 regular simultaneous poses, measure every A4 nonbody part after
        # the additional rigid drop against candidate body and cover.
        motion = []
        minima = {label: {"body_gap_mm": float("inf"), "cover_gap_mm": float("inf"),
                          "body_overlap_mm3": 0.0, "cover_overlap_mm3": 0.0}
                  for label in sorted(saved_module)}
        for fraction in FRACTIONS:
            state = {str(p.label): p.translate((0, 0, -DROP_A5))
                     for p in a4.components(fraction)}
            rows = []
            for label, part in state.items():
                body_gap = float(candidate_body.distance_to(part))
                cover_gap = float(cover.distance_to(part))
                body_ov = volume(candidate_body & part) if body_gap < CONTACT_TOL else 0.0
                cover_ov = volume(cover & part) if cover_gap < CONTACT_TOL else 0.0
                rec = {"label": label, "body_gap_mm": body_gap,
                       "body_overlap_mm3": body_ov, "cover_gap_mm": cover_gap,
                       "cover_overlap_mm3": cover_ov}
                rows.append(rec)
                minima.setdefault(label, {"body_gap_mm": float("inf"), "cover_gap_mm": float("inf"),
                                          "body_overlap_mm3": 0.0, "cover_overlap_mm3": 0.0})
                minima[label]["body_gap_mm"] = min(minima[label]["body_gap_mm"], body_gap)
                minima[label]["cover_gap_mm"] = min(minima[label]["cover_gap_mm"], cover_gap)
                minima[label]["body_overlap_mm3"] = max(minima[label]["body_overlap_mm3"], body_ov)
                minima[label]["cover_overlap_mm3"] = max(minima[label]["cover_overlap_mm3"], cover_ov)
            motion.append({"fraction": fraction, "parts": rows})
        report["candidate_motion_clearance"] = {
            "sample_count": len(motion), "fractions": [m["fraction"] for m in motion],
            "includes_all_21_regular_and_11_early_fractions": True,
            "regular_21_fractions": [i / 20 for i in range(21)],
            "additional_early_fractions": list(EARLY_FRACTIONS),
            "per_part_minimum_clearance_and_max_overlap": minima,
            "samples": motion,
        }
        stowed_parts = {str(p.label): p.translate((0, 0, -DROP_A5))
                        for p in a4.components(0.0)}
        envelope_by_part = {}
        envelope_parts = dict(stowed_parts)
        envelope_parts[BODY_LABEL] = candidate_body
        envelope_parts["trial_cover"] = cover
        for label, part in envelope_parts.items():
            b = bounds(part)
            envelope_by_part[label] = math.hypot(
                max(abs(b["y"][0]), abs(b["y"][1])),
                max(abs(b["z"][0]), abs(b["z"][1])))
        max_envelope = max(envelope_by_part.values())
        housing = stowed_parts["supported_housing"]
        housing_bounds = bounds(housing)
        floor_gap = float(candidate_body.distance_to(housing))
        floor_overlap = volume(candidate_body & housing) if floor_gap < CONTACT_TOL else 0.0
        report["frame_floor_contact"] = {
            "housing_bottom_z_mm": housing_bounds["z"][0],
            "expected_floor_z_mm": 57.75,
            "gap_mm": floor_gap,
            "overlap_mm3": floor_overlap,
            "pass": abs(housing_bounds["z"][0] - 57.75) <= CONTACT_TOL and
                    floor_gap <= CONTACT_TOL and floor_overlap < OVERLAP_TOL,
        }
        report["stowed_radial_envelope"] = {
            "radius_formula": "hypot(max(abs(Ybounds)), max(abs(Zbounds)))",
            "limit_mm_exclusive": 125.0,
            "radius_mm_by_part": envelope_by_part,
            "maximum_radius_mm": max_envelope,
            "pass": max_envelope < 125.0,
        }
        report["criteria_summary"] = {
            "body_single_valid_solid": body_metrics["single_positive_solid"],
            "cover_attaches_without_volume_overlap": body_cover_gap <= CONTACT_TOL and
                                                       body_cover_overlap < OVERLAP_TOL and
                                                       landing_band_volume > 0,
            "frame_floor_contact": report["frame_floor_contact"]["pass"],
            "stowed_radial_envelope": report["stowed_radial_envelope"]["pass"],
            "full_law_arc_radius_and_extrema_checks": all(
                x["sampled_1001_max_radius_error_mm"] < 1e-8 and
                x["analytic_extrema_bound_all_1001_angle_evaluations"]
                for x in arc_info.values()),
            "candidate_sampled_body_or_cover_interference": [
                {"fraction": m["fraction"], "part": p["label"],
                 "body_overlap_mm3": p["body_overlap_mm3"],
                 "cover_overlap_mm3": p["cover_overlap_mm3"]}
                for m in motion for p in m["parts"]
                if p["body_overlap_mm3"] >= OVERLAP_TOL or
                   p["cover_overlap_mm3"] >= OVERLAP_TOL],
            "original_A4_pin_body_interference_missed_by_regular_21": [
                row for row in report["original_A4_early_collision_summary"][
                    "nonzero_join_pin_body_overlap_samples"]
                if row["fraction"] not in {i / 20 for i in range(21)}],
        }
        report["passed_feasibility_probe"] = bool(
            report["criteria_summary"]["body_single_valid_solid"] and
            report["criteria_summary"]["cover_attaches_without_volume_overlap"] and
            report["criteria_summary"]["frame_floor_contact"] and
            report["criteria_summary"]["stowed_radial_envelope"] and
            report["criteria_summary"]["full_law_arc_radius_and_extrema_checks"] and
            not report["criteria_summary"]["candidate_sampled_body_or_cover_interference"])
    except Exception as exc:
        report["failures"].append({"error": repr(exc), "traceback": traceback.format_exc()})
        report["passed_feasibility_probe"] = False
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed_feasibility_probe": report.get("passed_feasibility_probe"),
        "report": str(OUT), "failures": report["failures"],
        "candidate_body": {k: report.get("candidate_body", {}).get(k)
                           for k in ("single_positive_solid", "solid_count", "volume_mm3", "bounds_mm")},
        "candidate_cover": report.get("candidate_cover", {}),
        "frame_floor_contact": report.get("frame_floor_contact", {}),
        "stowed_radial_envelope": report.get("stowed_radial_envelope", {}),
        "candidate_sample_count": report.get("candidate_motion_clearance", {}).get("sample_count"),
        "arc": report.get("full_law_arc", {}),
        "original_A4_early_collision_summary": report.get("original_A4_early_collision_summary", {}),
        "candidate_interference": report.get("criteria_summary", {}).get(
            "candidate_sampled_body_or_cover_interference", []),
    }, indent=2))
    return 0 if report.get("passed_feasibility_probe") else 1


if __name__ == "__main__":
    raise SystemExit(main())
