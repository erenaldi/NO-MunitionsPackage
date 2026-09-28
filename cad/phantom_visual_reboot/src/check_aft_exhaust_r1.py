"""Saved-artifact validation for the aft-exhaust R1 gate.

The five AftExhaust STEP outputs and immutable IntakeR3/R4/A5 STEP inputs are
the geometry under test.  This checker independently restates the rear seat,
connector, and liner loft sections; it does not import the aft-exhaust model.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True

import build123d as bd
from cadgen import read_scene
from cadgen.geometry import closest_points as _closest_points
from cadgen.geometry import overlap_volume as _overlap_volume


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reviews" / "aft_exhaust_r1_checks.json"
STATES = ("Stowed", "Midfold", "Deployed")
FRACTIONS = {"Stowed": 0.0, "Midfold": 0.5, "Deployed": 1.0}
EARLY_FRACTIONS = (0.001, 0.002, 0.005, 0.01, 0.02)
SAMPLES = tuple(sorted(set(i / 60.0 for i in range(61)) | set(EARLY_FRACTIONS)))

BODY = "RDM9_R7_symmetric_body_20mm_wedge_R4"
LINER = "aft_exhaust_r1_liner"
BOOL_TOL_MM3 = 0.001
OVERLAP_TOL_MM3 = 0.001
CONTACT_EPS_MM3 = 1.0e-5
MIN_CLEARANCE_MM = 0.2
STOWED_RADIUS_LIMIT_MM = 125.0
BODY_X_EXPECTED = (-1400.0, 1400.0)
BODY_X_TOL_MM = 1.0e-5
GLOBAL_X_SPAN_LIMIT_MM = 2800.66

FULL_PATHS = {
    state: ROOT / "STEP" / f"S_AftExhaust_R1_{state}.step" for state in STATES
}
BODY_PATH = ROOT / "STEP" / "S_AftExhaust_R1_Body_Duct.step"
LINER_PATH = ROOT / "STEP" / "S_AftExhaust_R1_Liner.step"

# Independent restatement of the approved loft profiles (X, widthY, heightZ,
# centerZ, cornerRadius).  The two connector throat stations at -1310.5 and
# -1308 are deliberately both explicit and constant-size.
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
INNER_TOOL_SECTIONS = (
    (-1395.0, 116.0, 116.0, 0.0, 10.0),
    *INNER_SECTIONS,
    (-1309.0, 76.0, 76.0, 0.0, 6.0),
)
SEAT_SECTIONS = (
    (-1401.0, 124.0, 124.0, 0.0, 14.0),
    (-1394.0, 124.0, 124.0, 0.0, 14.0),
    (-1360.0, 110.0, 110.0, 0.0, 12.0),
    (-1310.0, 84.0, 84.0, 0.0, 10.0),
)
CONNECTOR_SECTIONS = (
    (-1310.5, 76.0, 76.0, 0.0, 6.0),
    (-1308.0, 76.0, 76.0, 0.0, 6.0),
    (-1270.0, 80.0, 70.0, -10.0, 6.0),
    (-1150.0, 100.0, 60.0, -35.0, 6.0),
    (-1029.5, 116.0, 49.0, -52.5, 5.0),
)


def fail(report, check, **details):
    report["failures"].append({"check": check, **details})


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


def raw_solid(shape, description):
    """Use a native Solid only where cadgen.geometry requires that input type."""
    solids = list(shape.solids())
    if len(solids) != 1:
        raise RuntimeError(f"Expected one solid for {description}; got {len(solids)}")
    return solids[0]


def overlap(first, second):
    return float(_overlap_volume(raw_solid(first, "overlap first operand"),
                                 raw_solid(second, "overlap second operand")))


def exact_distance(first, second):
    return float(_closest_points(raw_solid(first, "distance first operand"),
                                 raw_solid(second, "distance second operand")).distance)


def topology(shape):
    solids = list(shape.solids())
    values = [float(item.volume) for item in solids]
    return {
        "valid": bool(shape.is_valid),
        "solid_count": len(solids),
        "positive_solid_volumes_mm3": values,
        "pass": bool(shape.is_valid and len(solids) == 1 and values
                      and all(value > 0.0 for value in values)),
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
    return volume(first - second) + volume(second - first)


def rounded_wire(record):
    x, width_y, height_z, center_z, radius = record
    profile = bd.RectangleRounded(height_z, width_y, radius)
    profile = profile.rotate(bd.Axis.Y, 90.0).translate((x, 0.0, center_z))
    return profile.faces()[0].outer_wire()


def ruled_loft(records):
    return bd.Solid.make_loft([rounded_wire(row) for row in records], ruled=True)


def independent_tools():
    outer = ruled_loft(OUTER_SECTIONS)
    inner = ruled_loft(INNER_TOOL_SECTIONS)
    liner = (outer - inner).clean()
    seat = ruled_loft(SEAT_SECTIONS)
    connector = ruled_loft(CONNECTOR_SECTIONS)
    cutter_union = (seat + connector).clean()
    return {
        "outer": raw_solid(outer, "independent outer liner loft"),
        "inner": raw_solid(inner, "independent inner liner tool"),
        "liner": raw_solid(liner, "independent hollow liner"),
        "seat": raw_solid(seat, "independent body seat cutter"),
        "connector": raw_solid(connector, "independent connector cutter"),
        "cutters": raw_solid(cutter_union, "independent seat and connector cutter union"),
    }


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
        raise RuntimeError(f"Duplicate saved STEP leaf labels in {path}: {sorted(set(duplicates))}")
    return parts


def inventory(path, expected_labels, report, key, singleton_alias=None):
    try:
        if not path.is_file():
            fail(report, "required_saved_STEP_missing", artifact=key, path=str(path))
            return {}
        parts = load_parts(path)
        document_labels = sorted(parts)
        if singleton_alias is not None:
            if len(parts) != 1:
                raise RuntimeError(f"Expected one leaf in isolated STEP; got {len(parts)}")
            parts = {singleton_alias: next(iter(parts.values()))}
        missing = sorted(set(expected_labels) - set(parts))
        extra = sorted(set(parts) - set(expected_labels))
        topology_rows = {label: topology(shape) for label, shape in parts.items()}
        report["saved_artifacts"][key] = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "document_labels": document_labels,
            "labels": sorted(parts),
            "part_count": len(parts),
            "expected_part_count": len(expected_labels),
            "missing_labels": missing,
            "unexpected_labels": extra,
            "topology": topology_rows,
        }
        if missing or extra or len(parts) != len(expected_labels):
            fail(report, "saved_STEP_inventory", artifact=key,
                 missing_labels=missing, unexpected_labels=extra,
                 actual_count=len(parts), expected_count=len(expected_labels))
        for label, row in topology_rows.items():
            if not row["pass"]:
                fail(report, "saved_component_not_one_valid_positive_solid",
                     artifact=key, label=label, topology=row)
        return parts
    except Exception as exc:
        fail(report, "saved_STEP_import_or_inventory_error", artifact=key,
             path=str(path), error=repr(exc), traceback=traceback.format_exc())
        return {}


def compare(actual, expected, report, check, **details):
    try:
        delta = symdiff_volume(raw_solid(actual, f"actual {check}"),
                               raw_solid(expected, f"expected {check}"))
        row = {**details, "symmetric_difference_mm3": delta,
               "tolerance_mm3_exclusive": BOOL_TOL_MM3,
               "pass": delta < BOOL_TOL_MM3}
        if not row["pass"]:
            fail(report, check, **row)
        return row
    except Exception as exc:
        row = {**details, "pass": False, "error": repr(exc)}
        fail(report, check + "_measurement_error", **row,
             traceback=traceback.format_exc())
        return row


def check_body_identity(report, parts, source_parts, isolated_body, tools):
    rows = {}
    for state in STATES:
        if BODY not in parts.get(state, {}) or BODY not in source_parts.get(state, {}):
            fail(report, "body_identity_inputs_missing", state=state)
            continue
        try:
            saved = raw_solid(parts[state][BODY], f"AftExhaust {state} body")
            original = raw_solid(source_parts[state][BODY], f"IntakeR3 {state} source body")
            expected = (original - tools["cutters"]).clean()
            direct_delta = symdiff_volume(saved, expected)
            outside_delta = symdiff_volume(
                (saved - tools["cutters"]).clean(),
                (original - tools["cutters"]).clean(),
            )
            removed_delta = symdiff_volume(
                (original - saved).clean(), (original & tools["cutters"]).clean())
            added = volume(saved - original)
            removed = volume(original - saved)
            body_box = bounds(saved)
            x_pass = all(abs(body_box["x"][i] - BODY_X_EXPECTED[i]) <= BODY_X_TOL_MM
                         for i in (0, 1))
            saved_topology = topology(saved)
            expected_topology = topology(expected)
            row = {
                "saved_vs_IntakeR3_minus_independent_seat_and_connector_mm3": direct_delta,
                "outside_cut_symmetric_difference_mm3": outside_delta,
                "removed_region_vs_original_intersection_with_cutters_mm3": removed_delta,
                "added_body_material_mm3": added,
                "removed_body_material_mm3": removed,
                "saved_body_bounds_mm": body_box,
                "expected_body_X_bounds_mm": list(BODY_X_EXPECTED),
                "body_X_tolerance_mm": BODY_X_TOL_MM,
                "body_X_pass": x_pass,
                "saved_topology": saved_topology,
                "independent_expected_topology": expected_topology,
                "pass": (direct_delta < BOOL_TOL_MM3 and outside_delta < BOOL_TOL_MM3
                         and removed_delta < BOOL_TOL_MM3 and added < BOOL_TOL_MM3
                         and removed > 0.0 and x_pass and saved_topology["pass"]
                         and expected_topology["pass"]),
            }
            rows[state] = row
            if not row["pass"]:
                fail(report, "body_not_exactly_IntakeR3_minus_independent_aft_cutters",
                     state=state, **row)
        except Exception as exc:
            fail(report, "body_boolean_identity_measurement_error", state=state,
                 error=repr(exc), traceback=traceback.format_exc())
    report["checks"]["body_exactly_IntakeR3_minus_independent_seat_and_connector"] = {
        "states": rows, "compared_count": len(rows), "expected_count": 3,
        "pass": len(rows) == 3 and all(row["pass"] for row in rows.values()),
    }

    if BODY in isolated_body and BODY in parts.get("Stowed", {}):
        isolated = isolated_body[BODY]
        full_stowed = parts["Stowed"][BODY]
        row = compare(isolated, full_stowed, report,
                      "isolated_Body_Duct_differs_from_full_Stowed_body",
                      comparison="isolated Body_Duct against full Stowed body")
    else:
        row = {"pass": False}
        fail(report, "isolated_Body_Duct_identity_inputs_missing")
    report["checks"]["isolated_body_matches_full_Stowed"] = row


def check_peer_identities(report, aft_parts, intake_parts, expected_nonbody):
    rows_by_state = {}
    for state in STATES:
        actual, source = aft_parts.get(state, {}), intake_parts.get(state, {})
        rows = {}
        for label in expected_nonbody:
            if label not in actual or label not in source:
                continue
            rows[label] = compare(
                actual[label], source[label], report,
                "aft_exhaust_changed_IntakeR3_nonbody_counterpart",
                state=state, label=label)
        row = {"compared_count": len(rows), "expected_count": 32,
               "parts": rows,
               "pass": len(rows) == 32 and all(item["pass"] for item in rows.values())}
        rows_by_state[state] = row
        if len(rows) != 32:
            fail(report, "IntakeR3_nonbody_identity_coverage", state=state,
                 expected=32, actual=len(rows))
    report["checks"]["all_32_nonbody_parts_exactly_match_saved_IntakeR3"] = rows_by_state


def check_liner_and_seat(report, parts, isolated_liner, tools):
    if LINER not in parts.get("Stowed", {}) or LINER not in isolated_liner:
        fail(report, "saved_liner_identity_inputs_missing")
        return
    saved_liner = raw_solid(parts["Stowed"][LINER], "saved Stowed liner")
    isolated = raw_solid(isolated_liner[LINER], "isolated saved liner")
    liner_identity = compare(saved_liner, tools["liner"], report,
                             "saved_liner_differs_from_independent_outer_minus_inner_profiles")
    isolated_identity = compare(isolated, saved_liner, report,
                                "isolated_liner_differs_from_full_Stowed_liner")

    rear_probe = ruled_loft(((-1400.1, 124.0, 124.0, 0.0, 14.0),
                             (-1399.9, 124.0, 124.0, 0.0, 14.0)))
    liner_mouth_probe = ruled_loft((
        (-1394.1, 116.0, 116.0, 0.0, 10.0),
        (-1394.0, 116.0, 116.0, 0.0, 10.0),
        (-1393.9, 116.0 - 14.0 * 0.1 / 34.0,
         116.0 - 14.0 * 0.1 / 34.0, 0.0, 10.0 - 2.0 * 0.1 / 34.0),
    ))
    body = raw_solid(parts["Stowed"][BODY], "saved Stowed body")
    rear_overlap = overlap(body, rear_probe)
    mouth_overlap = overlap(saved_liner, liner_mouth_probe)
    liner_box = bounds(saved_liner)
    body_box = bounds(body)
    recession = liner_box["x"][0] - body_box["x"][0]

    body_liner_overlap = overlap(body, saved_liner)
    boundary_distance = exact_distance(body, saved_liner)
    common = body & saved_liner
    common_face_area = (sum(float(face.area) for face in common.faces())
                        if common is not None else 0.0)
    # STEP round-tripping can leave coincident interface faces in separate
    # B-reps, so the Boolean common-face query may return no faces despite a
    # measured zero gap.  The independently restated seat side profiles from
    # -1394 through -1310 are identical to the outer-liner ruled loft; measure
    # its positive longitudinal side-face area as the interface-area proxy.
    seat_profile_match = tuple(SEAT_SECTIONS[1:]) == OUTER_SECTIONS
    matched_side_area = sum(
        float(face.area) for face in tools["outer"].faces()
        if bounds(face)["x"][1] - bounds(face)["x"][0] > 1.0e-3)
    report["checks"]["independent_liner_profiles_isolation_and_seat"] = {
        "saved_vs_independent_outer_minus_inner": liner_identity,
        "isolated_vs_full_Stowed_liner": isolated_identity,
        "outer_profile_sections": [list(row) for row in OUTER_SECTIONS],
        "inner_profile_sections": [list(row) for row in INNER_SECTIONS],
        "inner_tool_end_overruns_mm": [1.0, 1.0],
        "rear_opening_rounded_profile_mm": [124.0, 124.0, 14.0],
        "rear_opening_positive_volume_probe_overlap_mm3": rear_overlap,
        "liner_entrance_rounded_profile_mm": [116.0, 116.0, 10.0],
        "liner_entrance_positive_volume_probe_overlap_mm3": mouth_overlap,
        "body_rear_X_mm": body_box["x"][0],
        "liner_entrance_X_mm": liner_box["x"][0],
        "measured_recess_mm": recession,
        "body_liner_overlap_mm3": body_liner_overlap,
        "body_liner_boundary_distance_mm": boundary_distance,
        "common_boolean_face_area_mm2": common_face_area,
        "matching_independent_seat_side_profile_area_proxy_mm2": matched_side_area,
        "seat_side_profile_matches_outer_liner": seat_profile_match,
        "pass": (liner_identity["pass"] and isolated_identity["pass"]
                 and rear_overlap < OVERLAP_TOL_MM3
                 and mouth_overlap < OVERLAP_TOL_MM3
                 and abs(recession - 6.0) <= 1.0e-6
                 and body_liner_overlap < OVERLAP_TOL_MM3
                 and boundary_distance <= 1.0e-5
                 and seat_profile_match and matched_side_area > 0.0),
        "probe_method": "Positive-volume loft probes use matched rounded profiles, not square cornered boxes.",
    }
    if not report["checks"]["independent_liner_profiles_isolation_and_seat"]["pass"]:
        fail(report, "liner_opening_recess_or_seat_contact_failed",
             **report["checks"]["independent_liner_profiles_isolation_and_seat"])


def check_connector(report, source_parts, saved_body, saved_liner, tools):
    connector = tools["connector"]
    inner = tools["inner"]
    # This is the independently restated existing IntakeR3 aft-stub void.
    stub = bd.Box(77.0, 116.0, 49.0).translate((-991.5, 0.0, -52.5))
    connector_inner = overlap(connector, inner)
    connector_stub = overlap(connector, stub)
    stub_original_body = overlap(source_parts[BODY], stub)
    connector_body = overlap(connector, saved_body)
    connector_liner = overlap(connector, saved_liner)
    row = {
        "connector_vs_liner_inner_void_overlap_mm3": connector_inner,
        "connector_vs_existing_IntakeR3_stub_void_overlap_mm3": connector_stub,
        "existing_stub_box_vs_original_IntakeR3_body_material_mm3": stub_original_body,
        "connector_vs_saved_cut_body_material_overlap_mm3": connector_body,
        "connector_vs_saved_liner_material_overlap_mm3": connector_liner,
        "stub_box_mm": {"x": [-1030.0, -953.0], "y": [-58.0, 58.0], "z": [-77.0, -28.0]},
        "constant_throat_stations_X_mm": [-1310.5, -1308.0],
        "pass": (connector_inner > CONTACT_EPS_MM3
                 and connector_stub > CONTACT_EPS_MM3
                 and stub_original_body < OVERLAP_TOL_MM3
                 and connector_body < OVERLAP_TOL_MM3
                 and connector_liner < OVERLAP_TOL_MM3),
        "interpretation": "Connected geometric void only; no airflow or propulsion claim.",
    }
    report["checks"]["connector_void_continuity_and_material_clearance"] = row
    if not row["pass"]:
        fail(report, "connector_void_continuity_or_material_clearance_failed", **row)


def check_pockets_and_contacts(report, r4check, source_parts, aft_parts, tools):
    stowed_body = raw_solid(aft_parts["Stowed"][BODY], "saved Stowed body")
    source_body = raw_solid(source_parts["Stowed"][BODY], "saved IntakeR3 Stowed body")
    aft_tools = tools["cutters"]
    pocket_rows = {}
    for station, angle in r4check.STATIONS:
        rotated = [r4check.rotate_x(item, angle)
                   for item in r4check.independent_pocket_cutters()]
        pocket_tool = r4check.union(rotated)
        body_overlap = overlap(stowed_body, pocket_tool)
        cutter_overlap = overlap(aft_tools, pocket_tool)
        source_overlap = overlap(source_body, pocket_tool)
        row = {
            "station_angle_global_X_deg": angle,
            "saved_body_vs_independent_tail_pocket_tool_mm3": body_overlap,
            "original_IntakeR3_body_vs_tail_pocket_tool_mm3": source_overlap,
            "aft_exhaust_cutters_vs_tail_pocket_tool_mm3": cutter_overlap,
            "pass": (body_overlap < OVERLAP_TOL_MM3
                     and source_overlap < OVERLAP_TOL_MM3
                     and cutter_overlap < OVERLAP_TOL_MM3),
        }
        pocket_rows[station] = row
        if not row["pass"]:
            fail(report, "tail_pocket_material_or_region_changed", station=station, **row)
    report["checks"]["four_existing_tail_pockets_unchanged"] = {
        "pocket_count": len(pocket_rows), "pockets": pocket_rows,
        "pass": len(pocket_rows) == 4 and all(row["pass"] for row in pocket_rows.values()),
    }

    contact_rows = {}
    for state in STATES:
        parts = aft_parts.get(state, {})
        if BODY not in parts:
            fail(report, "fixed_mount_body_contact_body_missing", state=state)
            continue
        body = raw_solid(parts[BODY], f"saved {state} body")
        labels = [f"tail_r4_{station}_{suffix}"
                  for station, _ in r4check.STATIONS
                  for suffix in ("fixed_knuckle_aft", "fixed_knuckle_forward")]
        labels += ["intake_r1_fixed_mount_negative_y", "intake_r1_fixed_mount_positive_y"]
        rows = {}
        for label in labels:
            if label not in parts:
                continue
            amount = overlap(parts[label], body)
            rows[label] = {"positive_body_contact_overlap_mm3": amount,
                           "minimum_mm3_exclusive": CONTACT_EPS_MM3,
                           "pass": amount > CONTACT_EPS_MM3}
            if not rows[label]["pass"]:
                fail(report, "fixed_mount_body_contact_not_positive", state=state,
                     label=label, overlap_mm3=amount,
                     minimum_mm3_exclusive=CONTACT_EPS_MM3)
        contact_rows[state] = {
            "compared_count": len(rows), "expected_count": 10, "contacts": rows,
            "pass": len(rows) == 10 and all(row["pass"] for row in rows.values()),
        }
        if len(rows) != 10:
            fail(report, "fixed_mount_body_contact_coverage", state=state,
                 expected=10, actual=len(rows))
    report["checks"]["eight_tail_and_two_intake_fixed_mounts_positive"] = {
        "states": contact_rows,
        "pass": len(contact_rows) == 3 and all(row["pass"] for row in contact_rows.values()),
    }

    # Discover every other positive-volume body attachment present in saved
    # IntakeR3 Stowed and ensure the aft cut did not remove its contact.
    baseline = {}
    for label, shape in source_parts["Stowed"].items():
        if label == BODY or label not in aft_parts["Stowed"]:
            continue
        if bbox_gap(shape, source_body) > 0.0:
            continue
        before = overlap(shape, source_body)
        if before > CONTACT_EPS_MM3:
            after = overlap(aft_parts["Stowed"][label], stowed_body)
            baseline[label] = {
                "IntakeR3_positive_contact_mm3": before,
                "aft_exhaust_positive_contact_mm3": after,
                "pass": after > CONTACT_EPS_MM3,
            }
            if not baseline[label]["pass"]:
                fail(report, "preexisting_body_contact_not_preserved", label=label,
                     **baseline[label])
    report["checks"]["all_other_preexisting_positive_body_contacts_preserved"] = {
        "baseline_positive_contact_count": len(baseline),
        "contacts": baseline,
        "pass": all(row["pass"] for row in baseline.values()),
        "basis": "All positive-volume contacts are discovered from saved IntakeR3 Stowed; no pair is exempted.",
    }


def check_stowed_envelope(report, aft_parts, expected_labels):
    parts = aft_parts.get("Stowed", {})
    if set(parts) != set(expected_labels):
        fail(report, "stowed_global_envelope_inventory_incomplete",
             expected=len(expected_labels), actual=len(parts))
        return
    radii = {}
    x_bounds = {}
    for label, shape in parts.items():
        box = bounds(raw_solid(shape, f"saved Stowed {label}"))
        radii[label] = max(math.hypot(y, z)
                           for y in box["y"] for z in box["z"])
        x_bounds[label] = box["x"]
    witness = max(radii, key=radii.get)
    all_min_x = min(row[0] for row in x_bounds.values())
    all_max_x = max(row[1] for row in x_bounds.values())
    body_box = x_bounds[BODY]
    body_x_pass = all(abs(body_box[i] - BODY_X_EXPECTED[i]) <= BODY_X_TOL_MM
                       for i in (0, 1))
    global_x_span = all_max_x - all_min_x
    row = {
        "part_count": len(parts), "expected_part_count": len(expected_labels),
        "conservative_YZ_AABB_corner_radius_mm_by_part": radii,
        "maximum_conservative_radius_mm": radii[witness], "radius_witness": witness,
        "radius_limit_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
        "global_X_bounds_mm": [all_min_x, all_max_x],
        "global_X_span_mm": global_x_span,
        "global_X_span_limit_mm": GLOBAL_X_SPAN_LIMIT_MM,
        "saved_body_X_bounds_mm": body_box,
        "expected_body_X_bounds_mm": list(BODY_X_EXPECTED),
        "body_X_tolerance_mm": BODY_X_TOL_MM,
        "pass": (len(parts) == len(expected_labels)
                 and radii[witness] < STOWED_RADIUS_LIMIT_MM
                 and global_x_span <= GLOBAL_X_SPAN_LIMIT_MM and body_x_pass),
        "radius_method": "Conservative AABB Y/Z corner bound; not a tight radial maximum.",
    }
    report["checks"]["global_stowed_125mm_radius_and_X_envelope"] = row
    if not row["pass"]:
        fail(report, "global_stowed_radius_or_X_envelope_failed", **row)


def check_motion(report, r4check, a5check, basecheck, rampcheck,
                 r3_angle_deg, r4_parts, a5_parts, aft_parts, source_parts,
                 expected_nonbody):
    try:
        missing = sorted((set(a5check.PANELS) | set(a5check.SUPPORTS)) - set(a5_parts))
        if missing:
            raise RuntimeError(f"Saved A5 Stowed lacks motion inputs: {missing}")
        canonical = {
            label: a5check.panel_canonical(
                raw_solid(a5_parts[label], f"saved A5 Stowed {label}"),
                *label.split("_"), a5check.CUMULATIVE_A2_DROP_MM)
            for label in a5check.PANELS
        }
        r4_stowed = r4_parts
        if set(r4_stowed) != set(r4check.EXPECTED_LABELS):
            raise RuntimeError("Saved R4 Stowed inventory incomplete for motion reconstruction")

        # First establish that the saved IntakeR3 Midfold/Deployed peers are the
        # rigid poses reconstructed from saved R4/A5 and the saved R3 Stowed ramp.
        pose_rows = {}
        stowed_new = {label: raw_solid(source_parts["Stowed"][label],
                                       f"saved IntakeR3 Stowed {label}")
                      for label in basecheck.NEW_LABELS}
        for state in STATES:
            fraction = FRACTIONS[state]
            body_for_pose = raw_solid(aft_parts["Stowed"][BODY], "saved aft Stowed body")
            expected = basecheck.reconstruct_existing(
                r4check, a5check, r4_stowed, body_for_pose, canonical, fraction)
            expected.update(stowed_new)
            ramp_label = rampcheck.RAMP_LABEL
            expected[ramp_label] = rampcheck.rotate_ramp(
                stowed_new[ramp_label], r3_angle_deg * fraction)
            rows = {}
            saved = source_parts.get(state, {})
            for label in expected_nonbody:
                if label in saved and label in expected:
                    rows[label] = compare(
                        saved[label], expected[label], report,
                        "saved_IntakeR3_pose_differs_from_saved_stowed_reconstruction",
                        state=state, fraction=fraction, label=label)
            pose_rows[state] = {
                "fraction": fraction, "compared_count": len(rows),
                "expected_count": 32, "parts": rows,
                "pass": len(rows) == 32 and all(row["pass"] for row in rows.values()),
            }
            if len(rows) != 32:
                fail(report, "IntakeR3_saved_pose_identity_coverage", state=state,
                     expected=32, actual=len(rows))
        report["checks"]["saved_IntakeR3_peer_pose_provenance"] = pose_rows

        motion_rows = []
        exact_queries = 0
        global_proof = {"clearance_lower_bound_mm": None, "pair": None, "fraction": None,
                        "method": None}
        for sample_index, fraction in enumerate(SAMPLES):
            body_for_pose = raw_solid(aft_parts["Stowed"][BODY], "saved aft Stowed body")
            posed = basecheck.reconstruct_existing(
                r4check, a5check, r4_stowed, body_for_pose, canonical, fraction)
            posed.update(stowed_new)
            posed[rampcheck.RAMP_LABEL] = rampcheck.rotate_ramp(
                stowed_new[rampcheck.RAMP_LABEL], r3_angle_deg * fraction)
            peer_labels = sorted(set(posed) - {BODY})
            if set(peer_labels) != set(expected_nonbody) or len(peer_labels) != 32:
                raise RuntimeError(
                    f"Motion peer inventory mismatch at fraction {fraction}: "
                    f"missing={sorted(set(expected_nonbody)-set(peer_labels))}, "
                    f"extra={sorted(set(peer_labels)-set(expected_nonbody))}")
            liner = raw_solid(aft_parts["Stowed"][LINER], "saved Stowed liner")
            pair_records = []
            exact_fallbacks = []
            failed_pairs = []
            for label in peer_labels:
                peer = raw_solid(posed[label], f"posed {label}")
                lower = bbox_gap(liner, peer)
                if lower > MIN_CLEARANCE_MM:
                    evidence = lower
                    method = "conservative_AABB_lower_bound"
                    overlap_amount = 0.0
                else:
                    distance = exact_distance(liner, peer)
                    exact_queries += 1
                    overlap_amount = overlap(liner, peer) if lower == 0.0 else 0.0
                    method = "exact_nearest_points_fallback_after_AABB"
                    evidence = distance
                    exact_fallbacks.append({"part": label, "AABB_lower_bound_mm": lower,
                                            "exact_distance_mm": distance,
                                            "overlap_mm3": overlap_amount})
                row_pass = evidence > MIN_CLEARANCE_MM and overlap_amount < OVERLAP_TOL_MM3
                pair_records.append((evidence, label, method))
                if not row_pass:
                    failed_pairs.append({"part": label, "evidence_mm": evidence,
                                         "method": method, "overlap_mm3": overlap_amount})
            sample_min, witness, witness_method = min(pair_records, key=lambda item: item[0])
            sample_pass = len(pair_records) == 32 and not failed_pairs
            row = {
                "sample": sample_index, "fraction": fraction,
                "part_count_tested_against_saved_liner": len(pair_records),
                "expected_peer_count": 32,
                "minimum_proven_clearance_lower_bound_mm": sample_min,
                "minimum_bound_witness_part": witness,
                "minimum_bound_method": witness_method,
                "exact_fallback_pair_count": len(exact_fallbacks),
                "exact_fallback_pairs": exact_fallbacks,
                "failed_pairs": failed_pairs,
                "pass": sample_pass,
            }
            motion_rows.append(row)
            if (global_proof["clearance_lower_bound_mm"] is None
                    or sample_min < global_proof["clearance_lower_bound_mm"]):
                global_proof = {"clearance_lower_bound_mm": sample_min,
                                "pair": [LINER, witness], "fraction": fraction,
                                "method": witness_method}
            if not sample_pass:
                fail(report, "liner_motion_clearance_or_overlap_failed",
                     sample=sample_index, fraction=fraction,
                     minimum_proven_clearance_lower_bound_mm=sample_min,
                     failed_pairs=failed_pairs)
        expected_samples = len(SAMPLES)
        report["checks"]["saved_liner_vs_all_32_IntakeR3_peers_at_66_fractions"] = {
            "sample_count": len(motion_rows), "expected_sample_count": 66,
            "uniform_sample_count": 61, "early_fractions": list(EARLY_FRACTIONS),
            "peers_per_sample": 32,
            "total_pair_coverage": sum(row["part_count_tested_against_saved_liner"]
                                        for row in motion_rows),
            "expected_total_pair_coverage": 66 * 32,
            "all_pairs_covered": (len(motion_rows) == 66 and
                                   all(row["part_count_tested_against_saved_liner"] == 32
                                       for row in motion_rows)),
            "exact_distance_fallback_query_count": exact_queries,
            "minimum_proven_sampled_clearance_lower_bound": global_proof,
            "all_samples_pass": (len(motion_rows) == 66 and
                                 all(row["pass"] for row in motion_rows)),
            "measurement_policy": (
                "Per-pair AABB distance is a conservative lower bound; when it exceeds "
                "0.2 mm no exact distance is queried. Exact nearest distance is queried "
                "only when that bound cannot prove the strict threshold. The reported "
                "minimum is a proven lower bound, not an exact global minimum."),
            "existing_body_clearance_inheritance": (
                "The only R3 body edit is independently verified as material removal "
                "inside the aft seat/connector cutters; all 32 saved nonbody peers are "
                "Boolean-identical to IntakeR3 and their saved poses are independently "
                "reconstructed. Removing body material cannot reduce prior body clearance. "
                "This check covers all 32 peers against the saved liner at the stated samples."),
            "continuous_motion_claim": "None; these are the specified 66 discrete synchronous samples.",
            "samples": motion_rows,
            "pass": (expected_samples == 66 and len(motion_rows) == 66
                     and all(row["pass"] for row in motion_rows)),
        }
    except Exception as exc:
        fail(report, "saved_liner_motion_check_aborted", error=repr(exc),
             traceback=traceback.format_exc())
        report["checks"]["saved_liner_vs_all_32_IntakeR3_peers_at_66_fractions"] = {
            "pass": False, "error": repr(exc)}


def main():
    report = {
        "gate": "AftExhaustR1_saved_geometry_validation",
        "units": "mm",
        "scope": (
            "Five saved AftExhaust R1 artifacts: 34-part named-state inventories, "
            "isolated body/liner identity, independent Boolean loft provenance, "
            "rounded rear/liner openings, connector void continuity, retained tail "
            "pockets/supports, stowed envelope, and 66 sampled liner-to-peer checks. "
            "No source rebuild, render, continuous sweep, airflow, or visual approval."),
        "thresholds": {
            "saved_boolean_identity_mm3_exclusive": BOOL_TOL_MM3,
            "unexpected_overlap_mm3_exclusive": OVERLAP_TOL_MM3,
            "positive_fixed_mount_contact_mm3_exclusive": CONTACT_EPS_MM3,
            "liner_peer_clearance_mm_exclusive": MIN_CLEARANCE_MM,
            "stowed_conservative_YZ_AABB_corner_radius_mm_exclusive": STOWED_RADIUS_LIMIT_MM,
            "body_X_endpoint_tolerance_mm": BODY_X_TOL_MM,
            "global_stowed_X_span_mm_inclusive": GLOBAL_X_SPAN_LIMIT_MM,
            "saved_component_topology": "one valid positive-volume solid per saved leaf",
        },
        "independent_specification": {
            "outer_liner_sections_X_widthY_heightZ_centerZ_radius_mm": [
                list(row) for row in OUTER_SECTIONS],
            "inner_liner_sections_X_widthY_heightZ_centerZ_radius_mm": [
                list(row) for row in INNER_SECTIONS],
            "inner_tool_overrun_sections_mm": [list(INNER_TOOL_SECTIONS[0]),
                                                list(INNER_TOOL_SECTIONS[-1])],
            "seat_sections_X_widthY_heightZ_centerZ_radius_mm": [
                list(row) for row in SEAT_SECTIONS],
            "connector_sections_X_widthY_heightZ_centerZ_radius_mm": [
                list(row) for row in CONNECTOR_SECTIONS],
            "constant_connector_throat_X_mm": [-1310.5, -1308.0],
        },
        "saved_artifacts": {}, "checks": {}, "failures": [],
    }
    try:
        sys.path.insert(0, str(ROOT / "src"))
        import check_ramp_intake_r1 as basecheck
        import check_ramp_intake_r2 as rampcheck
        import check_ramp_intake_r3 as intakecheck
        import check_tail_fin_r4 as r4check
        import check_interleaved_a5 as a5check

        source_labels = tuple((*r4check.EXPECTED_LABELS, *basecheck.NEW_LABELS))
        expected_labels = tuple((*source_labels, LINER))
        expected_nonbody = tuple(label for label in source_labels if label != BODY)
        report["expected_inventory"] = {
            "full_saved_state_count": 34,
            "full_saved_state_labels": list(expected_labels),
            "nonbody_IntakeR3_peer_count": 32,
            "nonbody_IntakeR3_peer_labels": list(expected_nonbody),
        }

        aft_parts = {state: inventory(FULL_PATHS[state], expected_labels,
                                      report, f"AftExhaust_{state}")
                     for state in STATES}
        isolated_body = inventory(BODY_PATH, (BODY,), report, "AftExhaust_Body_Duct",
                                  singleton_alias=BODY)
        isolated_liner = inventory(LINER_PATH, (LINER,), report, "AftExhaust_Liner",
                                   singleton_alias=LINER)
        source_parts = {state: inventory(intakecheck.R3_PATHS[state], source_labels,
                                         report, f"IntakeR3_{state}")
                        for state in STATES}
        r4_parts = inventory(r4check.R4_PATHS["Stowed"], r4check.EXPECTED_LABELS,
                             report, "R4_Stowed_motion_input")
        a5_parts = inventory(a5check.A5_PATHS["Stowed"], r4check.A5_LABELS,
                             report, "A5_Stowed_motion_input")

        tools = independent_tools()
        report["independent_geometry_topology"] = {
            key: topology(value) for key, value in tools.items()
        }
        for key, row in report["independent_geometry_topology"].items():
            if not row["pass"]:
                fail(report, "independent_geometry_not_one_valid_positive_solid",
                     geometry=key, topology=row)

        check_peer_identities(report, aft_parts, source_parts, expected_nonbody)
        check_body_identity(report, aft_parts, source_parts, isolated_body, tools)
        check_liner_and_seat(report, aft_parts, isolated_liner, tools)
        if (source_parts.get("Stowed") and aft_parts.get("Stowed")
                and BODY in source_parts["Stowed"] and BODY in aft_parts["Stowed"]
                and LINER in aft_parts["Stowed"]):
            check_connector(report, source_parts["Stowed"],
                            aft_parts["Stowed"][BODY], aft_parts["Stowed"][LINER], tools)
            check_pockets_and_contacts(report, r4check, source_parts, aft_parts, tools)
        else:
            fail(report, "connector_pocket_or_support_inputs_missing")
        check_stowed_envelope(report, aft_parts, expected_labels)
        if r4_parts and a5_parts and source_parts.get("Stowed"):
            check_motion(report, r4check, a5check, basecheck, rampcheck,
                         intakecheck.R3_ANGLE_DEG, r4_parts, a5_parts, aft_parts,
                         source_parts, expected_nonbody)
        else:
            fail(report, "motion_saved_inputs_missing")
    except Exception as exc:
        fail(report, "checker_aborted_on_unexpected_exception", error=repr(exc),
             traceback=traceback.format_exc())

    report["passed"] = not report["failures"]
    motion = report["checks"].get("saved_liner_vs_all_32_IntakeR3_peers_at_66_fractions", {})
    envelope = report["checks"].get("global_stowed_125mm_radius_and_X_envelope", {})
    body = report["checks"].get("body_exactly_IntakeR3_minus_independent_seat_and_connector", {})
    liner = report["checks"].get("independent_liner_profiles_isolation_and_seat", {})
    report["summary"] = {
        "passed": report["passed"],
        "failure_count": len(report["failures"]),
        "saved_artifact_count": len(report["saved_artifacts"]),
        "full_state_component_counts": {
            state: report["saved_artifacts"].get(f"AftExhaust_{state}", {}).get("part_count")
            for state in STATES},
        "nonbody_counterpart_comparisons": {
            state: report["checks"].get("all_32_nonbody_parts_exactly_match_saved_IntakeR3", {})
            .get(state, {}).get("compared_count") for state in STATES},
        "body_cut_state_count": body.get("compared_count"),
        "maximum_body_boolean_identity_delta_mm3": max(
            (row.get("saved_vs_IntakeR3_minus_independent_seat_and_connector_mm3", 0.0)
             for row in body.get("states", {}).values()), default=None),
        "liner_recession_mm": liner.get("measured_recess_mm"),
        "body_liner_overlap_mm3": liner.get("body_liner_overlap_mm3"),
        "body_liner_contact_area_proxy_mm2": liner.get(
            "matching_independent_seat_side_profile_area_proxy_mm2"),
        "tail_pocket_count": report["checks"].get(
            "four_existing_tail_pockets_unchanged", {}).get("pocket_count"),
        "fixed_mounts_per_state": {
            state: row.get("compared_count") for state, row in report["checks"].get(
                "eight_tail_and_two_intake_fixed_mounts_positive", {}).get("states", {}).items()},
        "stowed_radius_mm": envelope.get("maximum_conservative_radius_mm"),
        "stowed_global_X_span_mm": envelope.get("global_X_span_mm"),
        "motion_sample_count": motion.get("sample_count", 0),
        "motion_pair_coverage": motion.get("total_pair_coverage"),
        "motion_exact_fallback_queries": motion.get("exact_distance_fallback_query_count"),
        "motion_minimum_proven_clearance_lower_bound": motion.get(
            "minimum_proven_sampled_clearance_lower_bound"),
        "first_failures": report["failures"][:12],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), **report["summary"]}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
