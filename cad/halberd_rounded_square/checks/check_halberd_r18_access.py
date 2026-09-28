"""Saved-artifact verification for the R18 access-feature pass.

Reads every saved STEP (full, separated, five focus crops) and their material
sidecars, rebuilds the source expectation from the approved 28-part base, and
compares. Every saved placement is checked (no sampling). Failures are
collected and reported; nothing is loosened to force a pass.
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cadgen import build123d as bd, read_scene
from cadgen.geometry import boundary_edges, self_intersections, topology_errors
from halberd_r17_interface_shapes import _slotted_head_local
from halberd_r18_access_build import (
    BOOSTER_HOST, CROP_BOUNDS, MAIN_HOST, NOZZLE_PARAMETERS, build_r18_access,
    metadata_crop_labels)
from halberd_r18_access_shapes import (
    APPROVED_BASE_HASH, BASELINE_STEP, load_manifest, load_saved_parts,
    measured_skin_point)

STEP = ROOT / "STEP"
REPORT_PATH = ROOT / "reviews" / "halberd_r18_access_checks.json"
TOL = 0.05          # mm^3 volume-difference tolerance
SEPARATION_X = -340.0
FAILURES: list = []
CROPS = {
    "F02": "halberd_r18_access_F02_focus",
    "forward_F04A_F03A": "halberd_r18_access_forward_F04A_F03A",
    "F04B": "halberd_r18_access_F04B_focus",
    "F05": "halberd_r18_access_F05_focus",
    "booster_F10_F03B": "halberd_r18_access_booster_F10_F03B",
}


def check(condition, message):
    if not condition:
        FAILURES.append(message if isinstance(message, str) else repr(message))
    return bool(condition)


def volume(shape):
    return shape.volume if shape else 0.0


def load(name):
    path = STEP / f"{name}.step"
    scene = read_scene(path)
    leaves = tuple(scene.leaves())
    parts = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in leaves}
    check(len(parts) == len(leaves), f"{name}: duplicate saved leaf labels")
    sidecar_path = Path(str(path) + ".json")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    check(sidecar.get("documentHash") == scene.document_hash,
          f"{name}: sidecar documentHash does not match saved STEP")
    return scene, parts, leaves, sidecar


def identical(actual, expected, label, context):
    added, missing = volume(actual - expected), volume(expected - actual)
    check(added < TOL and missing < TOL,
          f"{context}:{label}: geometry differs (extra {added:.4f}, missing {missing:.4f} mm3)")
    return added, missing


def solid_ok(shape, label):
    solids = shape.solids()
    ok = (shape.is_valid and len(solids) == 1 and solids[0].volume > 0.0 and
          not topology_errors(shape) and
          all(not boundary_edges(shell) for shell in shape.shells()) and
          not self_intersections(shape))
    check(ok, f"{label}: not a single positive closed clean solid")
    return ok


def boxes_overlap(a, b, pad=1e-4):
    x, y = a.bounding_box(optimal=False), b.bounding_box(optimal=False)
    return not (x.max.X < y.min.X - pad or y.max.X < x.min.X - pad or
                x.max.Y < y.min.Y - pad or y.max.Y < x.min.Y - pad or
                x.max.Z < y.min.Z - pad or y.max.Z < x.min.Z - pad)


def common_face_area(a, b):
    best = 0.0
    for fa in a.faces():
        for fb in b.faces():
            if boxes_overlap(fa, fb):
                common = fa & fb
                if common and common.area > best:
                    best = common.area
    return best


def color_text(shape):
    return None if shape.color is None else str(shape.color)


def assignments_by_label(scene, sidecar):
    table = sidecar["appearance"]["assignments"]
    return {leaf.label: table.get(leaf.ref.lstrip("#")) for leaf in scene.leaves()}


def expected_material(label):
    if label.endswith("_ring") or "terminal_" in label or "fastener_" in label:
        return "detail_metal"
    return "detail_paint"


def main():
    manifest = load_manifest()
    base_scene, base = load_saved_parts(BASELINE_STEP)
    check(base_scene.document_hash == APPROVED_BASE_HASH, "planning base hash changed")
    check(len(base) == 28, f"planning base part count {len(base)} != 28")

    print("Rebuilding source expectation (slow)...", flush=True)
    src = build_r18_access()
    new_labels = set(src.new_parts)
    hosts = {MAIN_HOST, BOOSTER_HOST}
    expected_full = set(base) | new_labels
    print(f"source: {len(base)} base + {len(new_labels)} new = {len(expected_full)}", flush=True)

    full_scene, full, full_leaves, full_sidecar = load("halberd_r18_access")
    sep_scene, sep, sep_leaves, sep_sidecar = load("halberd_r18_access_separated")
    check(set(full) == expected_full,
          f"full label set differs: missing {sorted(expected_full - set(full))} "
          f"extra {sorted(set(full) - expected_full)}")
    check(set(sep) == expected_full, "separated label set differs from full")

    # --- new parts: saved vs source identity, colour ------------------------
    identity = {}
    for label, part in src.new_parts.items():
        if label in full:
            identity[label] = identical(full[label], part, label, "full-vs-source")
            check(color_text(full[label]) == color_text(part), f"{label}: colour differs from source")

    # --- hosts: baseline minus declared cutters, zero gain -----------------
    host_report = {}
    for host in hosts:
        expected = base[host]
        for cutter in src.per_host_cutters[host]:
            expected = expected - cutter
        add, miss = identical(full[host], expected, host, "host=baseline-minus-cutters")
        gain = volume(full[host] - base[host])
        check(gain < TOL, f"{host}: gained {gain:.4f} mm3 beyond baseline")
        host_report[host] = {
            "baseline_volume_mm3": base[host].volume, "saved_volume_mm3": full[host].volume,
            "removed_mm3": base[host].volume - full[host].volume,
            "declared_cutters": len(src.per_host_cutters[host]),
            "extra_vs_expected_mm3": add, "missing_vs_expected_mm3": miss, "gain_mm3": gain}
        check(color_text(full[host]) == color_text(base[host]), f"{host}: colour changed")

    # --- other baseline parts (incl. five nose-joint parts) unchanged -------
    joint = sorted(l for l in base if l.startswith("main_joint_"))
    check(len(joint) == 5, f"expected five main_joint_* parts, found {len(joint)}")
    for label in sorted(set(base) - hosts):
        identical(full[label], base[label], label, "baseline-unchanged")
        check(color_text(full[label]) == color_text(base[label]), f"{label}: colour changed")

    # --- validity of every saved placement (full, separated, crops) ---------
    print(f"Validity of {len(full)} full placements...", flush=True)
    for label, shape in full.items():
        solid_ok(shape, f"full:{label}")
    print(f"Validity of {len(sep)} separated placements...", flush=True)
    for label, shape in sep.items():
        solid_ok(shape, f"separated:{label}")

    # --- support contact and overlap ---------------------------------------
    support = {}
    owner_shape = lambda label: full[src.owner_map[label]]
    for label in sorted(new_labels):
        host = owner_shape(label)
        overlap = volume(full[label] & host)
        check(overlap < TOL, f"{label}: overlaps owner host {overlap:.4f} mm3")
        area = common_face_area(full[label], host)
        gap = full[label].distance_to(host)
        check(area > 0.001, f"{label}: no support face contact with owner ({area})")
        check(gap < 1e-3, f"{label}: not touching owner (distance {gap})")
        support[label] = {"common_face_area_mm2": area, "distance_mm": gap}
    pair_overlaps = {}
    preexisting = {}
    checked_pairs = 0
    labels = list(full)
    for a, b in combinations(labels, 2):
        if not (a in new_labels or b in new_labels or a in hosts or b in hosts):
            continue
        if not boxes_overlap(full[a], full[b]):
            continue
        checked_pairs += 1
        overlap = volume(full[a] & full[b])
        if a in base and b in base:
            # Pair existed in the approved base: the pass must not add overlap.
            before = volume(base[a] & base[b])
            preexisting[f"{a}/{b}"] = {"base_mm3": before, "full_mm3": overlap}
            check(overlap <= before + TOL,
                  f"{a}/{b}: overlap grew {before:.4f} -> {overlap:.4f} mm3")
        elif overlap >= TOL:
            check(False, f"overlap {a}/{b}: {overlap:.4f} mm3")
            pair_overlaps[f"{a}/{b}"] = overlap
    # baseline pairs that are not touched by the pass keep the base checker's status.

    # --- slotted fasteners keep their slot ---------------------------------
    local_head, _ = _slotted_head_local()
    slot_report = {}
    for label in sorted(l for l in new_labels if "fastener_" in l):
        delta = abs(full[label].volume - local_head.volume)
        check(delta < TOL, f"{label}: slot/head volume {full[label].volume:.4f} != {local_head.volume:.4f}")
        slot_report[label] = delta

    # --- F03B central slot is open through the cap top ---------------------
    f03b = next(f for f in manifest["individual_access_features"] if f["id"] == "F03B")
    skin = measured_skin_point(base[BOOSTER_HOST], f03b["x"], f03b["tangent"], f03b["clock"])
    plane = bd.Plane(origin=skin["point"], x_dir=(1, 0, 0), z_dir=skin["normal"])
    cap = full["booster_r18_F03B_keyed_cap"]
    in_slot = plane.location * bd.Location((-0.5, 0.0, -0.40))
    beside = plane.location * bd.Location((-0.5, 3.0, -0.40))
    p_slot, p_side = in_slot.position, beside.position
    check(not cap.is_inside(p_slot), "F03B: slot centre probe is inside cap material (slot closed)")
    check(cap.is_inside(p_side), "F03B: cap material missing 3 mm beside slot")
    f03b_slot = {"slot_probe_empty": not cap.is_inside(p_slot), "beside_probe_solid": cap.is_inside(p_side)}

    # --- nozzle bores stay open, dark backs retained ------------------------
    nozzle_report = {}
    for key, host_label, dark in (
            ("main_nozzle", MAIN_HOST, ("main_nozzle_dark_recess", "main_nozzle_dark_floor")),
            ("booster_nozzle", BOOSTER_HOST, ("booster_nozzle_dark_recess", "booster_nozzle_dark_floor"))):
        p = NOZZLE_PARAMETERS[key]
        blockers = [full[l] for l in full if l in new_labels or l == host_label or l in dark]
        open_probes = 0
        for clock in range(0, 360, 45):
            import math
            for radius in (0.0, p["cavity_radius"] * 0.5, p["cavity_radius"] * 0.9):
                point = bd.Vector(p["mouth_x"] + 1.0, radius * math.sin(math.radians(clock)),
                                  radius * math.cos(math.radians(clock)))
                if not full[host_label].is_inside(point) and not any(
                        full[l].is_inside(point) for l in new_labels
                        if l.startswith(key.split("_")[0] + "_r18_nozzle")):
                    open_probes += 1
        check(open_probes == 8 * 3, f"{key}: bore blocked ({open_probes}/24 open probes)")
        for label in dark:
            check(label in full, f"{label}: dark back part missing")
            if label in full:
                identical(full[label], base[label], label, "nozzle-dark-back")
        nozzle_report[key] = {"open_probes": open_probes, "dark_parts": list(dark)}

    # --- lengths and separation -------------------------------------------
    full_box, sep_box = full_scene.roots[0].shape().bounding_box(), sep_scene.roots[0].shape().bounding_box()
    length_full = full_box.size.X
    check(abs(length_full - 3370.0) < 0.01, f"full length {length_full} != 3370")
    moved = 0
    for label in full:
        is_booster = label == BOOSTER_HOST or label.startswith("booster_")
        expected = full[label].moved(bd.Location((SEPARATION_X if is_booster else 0.0, 0, 0)))
        identical(sep[label], expected, label, "separated")
        if is_booster:
            moved += 1
            a, b = full[label].bounding_box(), sep[label].bounding_box()
            check(abs((b.min.X - a.min.X) - SEPARATION_X) < 1e-3, f"{label}: not moved {SEPARATION_X} X")
        else:
            a, b = full[label].bounding_box(), sep[label].bounding_box()
            check(abs(b.min.X - a.min.X) < 1e-3, f"{label}: non-booster part moved")
    check(moved > 0, "no booster parts moved")

    # --- material sidecars --------------------------------------------------
    mat_full = assignments_by_label(full_scene, full_sidecar)
    mats = full_sidecar["appearance"]["materials"]
    for label in new_labels:
        want = expected_material(label)
        got = mat_full.get(label)
        check(got is not None and (got == want or mats.get(got, {}).get("name") == want),
              f"{label}: material {got!r} != {want}")

    # --- focus crops --------------------------------------------------------
    crop_report = {}
    for variant, name in CROPS.items():
        scene, parts, leaves, sidecar = load(name)
        want = metadata_crop_labels(variant)
        check(set(parts) == set(want) and len(parts) == len(want),
              f"{name}: labels {sorted(parts)} != {sorted(want)}")
        lo, hi = CROP_BOUNDS[variant]
        host_label = BOOSTER_HOST if variant.startswith("booster") else MAIN_HOST
        crop_host = parts.get(f"{host_label}_r18_crop_{variant}")
        if crop_host is not None:
            box = full[host_label].bounding_box()
            clip = bd.Box(hi - lo, box.size.Y + 2.0, box.size.Z + 2.0).translate(
                ((lo + hi) / 2.0, (box.min.Y + box.max.Y) / 2.0, (box.min.Z + box.max.Z) / 2.0))
            identical(crop_host, full[host_label] & clip, "crop_host", name)
        for label, shape in parts.items():
            solid_ok(shape, f"{name}:{label}")
            if label in full and label not in hosts:
                identical(shape, full[label], label, f"{name}-vs-full")
        mat_assign = assignments_by_label(scene, sidecar)
        for label in parts:
            if label in new_labels:
                got = mat_assign.get(label)
                w = expected_material(label)
                check(got is not None and (got == w or sidecar["appearance"]["materials"].get(got, {}).get("name") == w),
                      f"{name}:{label}: material {got!r} != {w}")
        crop_report[variant] = {"step": f"STEP/{name}.step", "parts": len(parts),
                                "axial_bounds_mm": [lo, hi], "document_hash": scene.document_hash}

    report = {
        "status": "PASS" if not FAILURES else "FAIL",
        "failures": FAILURES,
        "base_hash": base_scene.document_hash,
        "full": {"step": "STEP/halberd_r18_access.step", "hash": full_scene.document_hash,
                 "parts": len(full), "base_parts": len(base), "new_parts": len(new_labels),
                 "access_feature_parts": sum(len(v) for v in src.feature_map.values()),
                 "nozzle_parts": len(new_labels) - sum(len(v) for v in src.feature_map.values()),
                 "length_x_mm": length_full},
        "separated": {"step": "STEP/halberd_r18_access_separated.step", "hash": sep_scene.document_hash,
                      "parts": len(sep), "booster_parts_moved": moved, "delta_x_mm": SEPARATION_X,
                      "length_x_mm": sep_box.size.X},
        "hosts": host_report,
        "nose_joint_parts_unchanged": joint,
        "support": support,
        "overlap_pairs_tested": checked_pairs,
        "overlap_violations": pair_overlaps,
        "baseline_pair_overlaps_base_vs_full": preexisting,
        "fastener_slot_volume_delta_mm3": slot_report,
        "f03b_central_slot": f03b_slot,
        "nozzle": nozzle_report,
        "new_part_identity_delta_mm3": {k: list(v) for k, v in identity.items()},
        "crops": crop_report,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "failures", "full", "separated")}, indent=2))
    print(("PASS" if not FAILURES else "FAIL") + f": R18 access saved-artifact checks; report={REPORT_PATH}")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
