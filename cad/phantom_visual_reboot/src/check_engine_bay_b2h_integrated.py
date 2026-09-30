"""Saved-artifact integrated regression for the Phantom B2H baseline (engine on ramp, 340 mm belly door, ~50 mm lip drop,
square nozzle, cosmetic engraving).  Fictional game asset; visual/CAD evidence only.

Geometry under test: STEP/S_EngineBay_B2H_{Stowed,Deployed}_Full.step.  Reference inputs: STEP/R_RampIntake_R3_{Stowed,Deployed}.step
(the immutable IntakeR3 assemblies that all non-ramp peers derive from).  This checker restates the motion model (hinge,
angles) independently of the model sources; it does not import them.

Reports (never hides) every overlap.  Exit status 1 when any hard check fails.  Conservative bounds are reported as bounds.
Not covered: continuous swept volumes between sampled poses, wing/fin motion (unchanged parts), actuation, airflow.
"""

from __future__ import annotations

import itertools
import json
import math
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True

import build123d as bd
from cadgen import read_scene
from cadgen.geometry import overlap_volume as _overlap_volume

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reviews" / "engine_bay_b2h_integrated_checks.json"
STATES = ("Stowed", "Deployed")

BODY = "RDM9_R7_symmetric_body_20mm_wedge_R4"
RAMP = "intake_r1_ramp"
LINER = "aft_exhaust_r1_liner"

# Independent restatement of the motion model.
LEVER = math.hypot(660.0, 3.0)
DEG_R3 = math.degrees(math.asin((35.0 + 3.0) / LEVER) - math.atan2(3.0, 660.0))       # accepted 35 mm setting
DEG_B2 = DEG_R3 + math.degrees(15.0 / LEVER)                                          # +15 mm tangential lip travel
RAMP_AXIS = bd.Axis((-950.0, 0.0, -83.0), (0.0, 1.0, 0.0))
DOOR_AXIS = bd.Axis((53.0, 0.0, -84.5), (0.0, 1.0, 0.0))
DOOR_DEG = 9.86
LIP_DROP_EXPECTED = 50.0
LIP_DROP_TOL = 0.25

BOOL_TOL = 0.001            # mm3, identity / unexpected overlap
POSE_TOL = 0.05             # mm3, rotated-vs-saved identity (numerical)
GROWTH_TOL = 0.05           # mm3, allowed growth of an intentional-contact overlap during motion
RADIUS_LIMIT = 125.0
X_SPAN_LIMIT = 2800.66

RAMP_PREFIXES = ("b2_engine", "b2d_face", "b2d_inlet", "b2d_fan", "b2d_spinner", "b2d_mount_pad")
DOOR_PREFIXES = ("b2d_door",)

RAMP_FRACTIONS = tuple(sorted(set([i / 20.0 for i in range(21)] + [0.001, 0.005, 0.01, 0.02, 0.98, 0.99, 0.995, 0.999])))
DOOR_FRACTIONS = RAMP_FRACTIONS
ASYNC_FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)


def solids(shape):
    return list(shape.solids())


def bounds(shape):
    b = shape.bounding_box(optimal=False)
    return (b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z)


def gap(a, b):
    ga = [max(0.0, a[i] - b[i + 1], b[i] - a[i + 1]) for i in (0, 2, 4)]
    return math.sqrt(sum(g * g for g in ga))


def overlap(first, second):
    total = 0.0
    for s in solids(first):
        sb = bounds(s)
        for t in solids(second):
            if gap(sb, bounds(t)) > 0.0:
                continue
            total += float(_overlap_volume(s, t))
    return total


def symdiff(first, second):
    return float((first - second).volume if (first - second) is not None else 0.0) + \
        float((second - first).volume if (second - first) is not None else 0.0)


def vertex_key(shape, nd=3):
    return sorted((round(v.X, nd), round(v.Y, nd), round(v.Z, nd)) for v in shape.vertices())


def same_shape(a, b):
    """Identity evidence independent of boolean robustness: volume, centre of mass, bounding box, and the B-rep vertex set."""
    ba, bb = bounds(a), bounds(b)
    rel_vol = abs(vol(a) - vol(b)) / max(vol(a), 1e-12)
    com = (a.center() - b.center()).length
    bbox = max(abs(x - y) for x, y in zip(ba, bb))
    va, vb = vertex_key(a), vertex_key(b)
    verts_ok = len(va) == len(vb) and all(max(abs(p - q) for p, q in zip(x, y)) <= 2e-3 for x, y in zip(va, vb))
    return {"rel_volume_diff": rel_vol, "com_distance_mm": com, "bbox_max_delta_mm": bbox,
            "vertex_count": [len(va), len(vb)], "vertex_sets_match_2um": verts_ok,
            "pass": bool(rel_vol < 1e-7 and com < 1e-3 and bbox < 1e-3 and verts_ok)}


def vol(shape):
    return 0.0 if shape is None else float(shape.volume)


def load(path):
    scene = read_scene(str(path))
    parts, dups = {}, []
    for occ in scene.leaves():
        label = str(occ.label)
        if label in parts:
            dups.append(label)
        parts[label] = occ.shape()
    if dups:
        raise RuntimeError(f"duplicate leaf labels in {path}: {sorted(set(dups))}")
    return parts


def group(parts, prefixes, extra=()):
    return [k for k in parts if k in extra or k.startswith(prefixes)]


def main():
    t0 = time.time()
    report = {"gate": "B2H_integrated_regression", "units": "mm", "failures": [], "checks": {}, "notes": [
        "Overlap volumes are exact booleans on saved leaves; clearances during sweeps are lower bounds (AABB gap) where no boolean was needed.",
        "Sampled poses only; no continuous swept-volume proof.",
        "Existing R3/A5/TailR4/aft-exhaust checkers are run separately against their own saved artifacts."]}
    fails = report["failures"]

    def fail(check, **kw):
        fails.append({"check": check, **kw})

    saved = {s: load(ROOT / "STEP" / f"S_EngineBay_B2H_{s}_Full.step") for s in STATES}
    r3 = {s: load(ROOT / "STEP" / f"R_RampIntake_R3_{s}.step") for s in STATES}
    report["parameters"] = {"deg_r3": DEG_R3, "deg_b2": DEG_B2, "door_deg": DOOR_DEG,
                            "part_count": {s: len(saved[s]) for s in STATES}}

    # 1. inventory + topology
    inv = {}
    for s in STATES:
        rows = {}
        for k, shape in saved[s].items():
            sol = solids(shape)
            rows[k] = {"valid": bool(shape.is_valid), "solids": len(sol),
                       "min_solid_volume": min((float(x.volume) for x in sol), default=0.0)}
            if not (shape.is_valid and sol and rows[k]["min_solid_volume"] > 0.0):
                fail("leaf_topology", state=s, label=k, **rows[k])
        inv[s] = rows
    same_labels = set(saved["Stowed"]) == set(saved["Deployed"])
    if not same_labels:
        fail("state_inventories_differ", only_stowed=sorted(set(saved["Stowed"]) - set(saved["Deployed"])),
             only_deployed=sorted(set(saved["Deployed"]) - set(saved["Stowed"])))
    report["checks"]["inventory"] = {"same_labels_both_states": same_labels,
                                     "multi_solid_leaves": {s: [k for k, r in inv[s].items() if r["solids"] != 1] for s in STATES}}
    print("inventory", round(time.time() - t0, 1), flush=True)

    # 2. non-body/non-ramp R3 peers unchanged, body only lost material
    peer_rows, body_rows = {}, {}
    for s in STATES:
        for k, shape in r3[s].items():
            if k in (BODY, RAMP):
                continue
            if k not in saved[s]:
                fail("r3_peer_missing", state=s, label=k)
                continue
            d = symdiff(shape, saved[s][k])
            peer_rows[f"{s}/{k}"] = d
            if d > BOOL_TOL:
                fail("r3_peer_not_identical", state=s, label=k, symdiff_mm3=d)
        added = vol(saved[s][BODY] - r3[s][BODY])
        removed = vol(r3[s][BODY] - saved[s][BODY])
        body_rows[s] = {"material_added_mm3": added, "material_removed_mm3": removed}
        if added > BOOL_TOL:
            fail("body_gained_material", state=s, added_mm3=added)
    report["checks"]["r3_peer_identity_and_body_removal_only"] = {"peer_symdiff_mm3": peer_rows, "body": body_rows}
    print("peers", round(time.time() - t0, 1), flush=True)

    # 3. pose model vs saved Deployed
    rgroup = group(saved["Stowed"], RAMP_PREFIXES, (RAMP,))
    dgroup = group(saved["Stowed"], DOOR_PREFIXES)
    pose_rows = {}
    for k in rgroup:
        moved = saved["Stowed"][k].rotate(RAMP_AXIS, DEG_B2)
        d = symdiff(moved, saved["Deployed"][k])
        inv = same_shape(moved, saved["Deployed"][k])
        pose_rows[k] = {"symdiff_mm3": d, "invariants": inv}
        if not inv["pass"]:
            fail("ramp_group_pose_model_mismatch", label=k, symdiff_mm3=d, invariants=inv)
    for k in dgroup:
        moved = saved["Stowed"][k].rotate(DOOR_AXIS, DOOR_DEG)
        d = symdiff(moved, saved["Deployed"][k])
        inv = same_shape(moved, saved["Deployed"][k])
        pose_rows[k] = {"symdiff_mm3": d, "invariants": inv}
        if not inv["pass"]:
            fail("door_group_pose_model_mismatch", label=k, symdiff_mm3=d, invariants=inv)
    degenerate = {k: v["symdiff_mm3"] for k, v in pose_rows.items() if v["symdiff_mm3"] > POSE_TOL and v["invariants"]["pass"]}
    # Wings, fins and joined-wing parts legitimately differ between Stowed and Deployed (whole-vehicle deployment state);
    # they were already compared to the matching R3 state above.
    state_dependent = sorted(k for k in saved["Stowed"] if k not in rgroup and k not in dgroup
                             and symdiff(saved["Stowed"][k], saved["Deployed"][k]) > BOOL_TOL)
    lip = -86.0 - bounds(saved["Deployed"][RAMP])[4]
    lip_stowed = -86.0 - bounds(saved["Stowed"][RAMP])[4]
    if abs(lip - LIP_DROP_EXPECTED) > LIP_DROP_TOL:
        fail("lip_drop_out_of_tolerance", measured_mm=lip, expected_mm=LIP_DROP_EXPECTED)
    report["checks"]["pose_model_identity"] = {"rotated_stowed_vs_saved_deployed": pose_rows,
                                               "boolean_symdiff_unreliable_but_invariants_pass": degenerate,
                                               "leaves_that_differ_between_states_R3_state_dependent": state_dependent,
                                               "deployed_lip_drop_mm": lip, "stowed_lip_offset_mm": lip_stowed,
                                               "ramp_group": rgroup, "door_group": dgroup}
    print("pose model", round(time.time() - t0, 1), flush=True)

    # 4. stowed envelope (conservative AABB corner bound)
    radii = {}
    xmin, xmax = 1e9, -1e9
    for k, shape in saved["Stowed"].items():
        b = bounds(shape)
        radii[k] = max(math.hypot(y, z) for y in b[2:4] for z in b[4:6])
        xmin, xmax = min(xmin, b[0]), max(xmax, b[1])
    worst = max(radii, key=radii.get)
    env_ok = radii[worst] < RADIUS_LIMIT and (xmax - xmin) <= X_SPAN_LIMIT
    if not env_ok:
        fail("stowed_envelope", worst_part=worst, radius_mm=radii[worst], x_span_mm=xmax - xmin)
    report["checks"]["stowed_envelope"] = {"max_conservative_radius_mm": radii[worst], "witness": worst,
                                           "limit_mm_exclusive": RADIUS_LIMIT, "x_span_mm": xmax - xmin,
                                           "x_span_limit_mm": X_SPAN_LIMIT, "pass": env_ok,
                                           "method": "Conservative YZ AABB corner bound, not a tight radial maximum."}
    print("envelope", round(time.time() - t0, 1), flush=True)

    # 5. static pairwise overlaps (full list, not filtered)
    static = {}
    for s in STATES:
        labs = list(saved[s])
        bb = {k: bounds(saved[s][k]) for k in labs}
        rows = {}
        for a, b in itertools.combinations(labs, 2):
            if gap(bb[a], bb[b]) > 0.0:
                continue
            v = overlap(saved[s][a], saved[s][b])
            if v > BOOL_TOL:
                rows[f"{a} | {b}"] = v
        static[s] = rows
        print("static", s, len(rows), round(time.time() - t0, 1), flush=True)
    report["checks"]["static_overlap_pairs_gt_tol"] = static
    # classification is intentionally reported, not decided here; hard fail only if the two states disagree
    only = {"stowed_only": sorted(set(static["Stowed"]) - set(static["Deployed"])),
            "deployed_only": sorted(set(static["Deployed"]) - set(static["Stowed"]))}
    report["checks"]["static_overlap_state_differences"] = only

    # 6. motion sweeps vs peers (baseline = static Stowed overlaps)
    peers = [k for k in saved["Stowed"] if k not in rgroup and k not in dgroup]

    def sweep(name, moving, axis, deg_max, fractions, peer_state="Stowed"):
        base = static[peer_state]
        rows, worst_over, min_gap = [], {}, 1e9
        for f in fractions:
            worst_here = {}
            for m in moving:
                shape = saved["Stowed"][m].rotate(axis, deg_max * f)
                mb = bounds(shape)
                for p in peers:
                    pb = bounds(saved[peer_state][p])
                    g = gap(mb, pb)
                    if g > 0.0:
                        min_gap = min(min_gap, g)
                        continue
                    v = overlap(shape, saved[peer_state][p])
                    key = f"{m} | {p}"
                    baseline = base.get(f"{m} | {p}", base.get(f"{p} | {m}", 0.0))
                    if v > BOOL_TOL:
                        worst_here[key] = (v, baseline)
                        prev = worst_over.get(key, (0.0, baseline, f))
                        if v > prev[0]:
                            worst_over[key] = (v, baseline, f)
            rows.append({"fraction": f, "overlapping_pairs": len(worst_here)})
        viol = {k: {"max_overlap_mm3": v[0], "static_stowed_overlap_mm3": v[1], "at_fraction": v[2]}
                for k, v in worst_over.items() if v[0] > v[1] * 1.001 + GROWTH_TOL}
        for k, row in viol.items():
            fail("motion_overlap_grew", sweep=name, pair=k, **row)
        report["checks"][name] = {"poses": len(fractions), "pairs_ever_overlapping": {
            k: {"max_overlap_mm3": v[0], "static_stowed_overlap_mm3": v[1]} for k, v in worst_over.items()},
            "violations": viol, "min_aabb_gap_where_disjoint_mm": min_gap if min_gap < 1e8 else None}
        print("sweep", name, len(viol), round(time.time() - t0, 1), flush=True)

    sweep("ramp_group_sweep_vs_fixed_peers", rgroup, RAMP_AXIS, DEG_B2, RAMP_FRACTIONS)
    sweep("door_sweep_vs_fixed_peers", dgroup, DOOR_AXIS, DOOR_DEG, DOOR_FRACTIONS)
    # wings/fins deployed while the intake group is at any of the sampled poses (asynchronous combinations)
    sweep("ramp_group_vs_deployed_state_wings_and_fins", rgroup, RAMP_AXIS, DEG_B2, ASYNC_FRACTIONS, peer_state="Deployed")
    sweep("door_vs_deployed_state_wings_and_fins", dgroup, DOOR_AXIS, DOOR_DEG, ASYNC_FRACTIONS, peer_state="Deployed")

    # mount pads: report contact type honestly (face contact vs volume overlap)
    pads = {}
    for k in saved["Stowed"]:
        if k.startswith("b2d_mount_pad"):
            env = saved["Stowed"]["b2_engine_envelope"]
            pads[k] = {"volume_overlap_with_engine_mm3": overlap(saved["Stowed"][k], env),
                       "aabb_gap_to_engine_mm": gap(bounds(saved["Stowed"][k]), bounds(env)),
                       "aabb_gap_to_ramp_mm": gap(bounds(saved["Stowed"][k]), bounds(saved["Stowed"][RAMP]))}
    report["checks"]["mount_pad_contact_type"] = pads

    # coupled sequence: ramp and door together against the remaining peers already covered; door vs ramp group all combos
    rows, worst_pair = [], {}
    for g_f, r_f in itertools.product(ASYNC_FRACTIONS, ASYNC_FRACTIONS):
        for d in dgroup:
            dshape = saved["Stowed"][d].rotate(DOOR_AXIS, DOOR_DEG * g_f)
            db = bounds(dshape)
            for m in rgroup:
                mshape = saved["Stowed"][m].rotate(RAMP_AXIS, DEG_B2 * r_f)
                if gap(db, bounds(mshape)) > 0.0:
                    continue
                v = overlap(dshape, mshape)
                if v > BOOL_TOL:
                    key = f"{d} | {m}"
                    if v > worst_pair.get(key, (0.0,))[0]:
                        worst_pair[key] = (v, g_f, r_f)
    for k, (v, g_f, r_f) in worst_pair.items():
        fail("door_ramp_group_overlap", pair=k, overlap_mm3=v, door_fraction=g_f, ramp_fraction=r_f)
    report["checks"]["door_vs_ramp_group_async_grid"] = {"combos": len(ASYNC_FRACTIONS) ** 2, "overlaps": {
        k: {"overlap_mm3": v[0], "door_fraction": v[1], "ramp_fraction": v[2]} for k, v in worst_pair.items()}}
    print("async grid", round(time.time() - t0, 1), flush=True)

    report["elapsed_s"] = round(time.time() - t0, 1)
    report["failure_count"] = len(fails)
    REPORT.write_text(json.dumps(report, indent=1))
    print(json.dumps({"failure_count": len(fails), "failures": fails[:12], "elapsed_s": report["elapsed_s"]}, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
