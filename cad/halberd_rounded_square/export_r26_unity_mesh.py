"""Export the accepted R26 Halberd (rounded-square study) as deterministic Unity OBJ groups.

Candidate staging only: output goes to cad/candidates/halberd_r26 and never under the Unity tree.
Axis map CAD (X,Y,Z) -> Unity (Y,Z,X), millimetres -> metres (same contract as cad/halberd).
Every leaf label must map to exactly one group; the export fails on unclassified, missing or empty groups.
Usage: python export_r26_unity_mesh.py [tolerance_mm=0.12] [angular_rad=0.3]
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import trimesh
from cadgen import read_scene

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "STEP" / "r26_nozzle_recess.step"
OUT_DIR = HERE.parent / "candidates" / "halberd_r26"
UNITY_ROOT = HERE.parents[1] / "unity"
TOLERANCE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.12
ANGULAR = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
MM = 0.001
TRIANGLE_CEILING = 1000000   # guard only; the shipping budget is an open user decision
EXPECTED_LEAVES = 383
EXPECTED_HALF_LENGTH_MM = 1685.0
STAGE_SEAM_X_MM = -1123.3   # booster/main split (CAD X)
UPPER = ("body", "intake_recess", "sustainer_fins", "hardware_main", "sustainer_nozzle")
BOOSTER = ("booster_body", "booster_fins", "hardware_booster", "booster_nozzle")
OUTPUTS = {g: f"HalberdR26_{''.join(p.title() for p in g.split('_'))}.obj" for g in UPPER + BOOSTER}


def classify(label):
    if label in ("main_body_intake_r12", "main_ogive") or label.startswith("main_joint_liner"):
        return "body"
    if label.startswith("main_intake_dark"):
        return "intake_recess"
    if label.startswith("main_fin_"):
        return "sustainer_fins"
    if label.startswith("main_nozzle_dark"):
        return "sustainer_nozzle"
    if label == "booster_body":
        return "booster_body"
    if label.startswith("booster_fin_fairing"):
        return "booster_fins"
    if label.startswith("booster_nozzle_dark"):
        return "booster_nozzle"
    if label.startswith("main_joint_fastener") or re.match(r"(main|booster)_r\d+", label):
        return "hardware_main" if label.startswith("main") else "hardware_booster"
    raise ValueError(f"unclassified leaf label: {label}")


HARDWARE_TESSELLATION = (0.3, 0.6)   # screws/covers: coarser (user-approved guidance), body keeps (TOLERANCE, ANGULAR)


def to_unity(shape, tess):
    verts, tris = shape.tessellate(*tess)
    cad = np.array([(v.X, v.Y, v.Z) for v in verts], dtype=float)
    game = np.column_stack((cad[:, 1], cad[:, 2], cad[:, 0])) * MM
    return trimesh.Trimesh(vertices=game, faces=np.asarray(tris), process=False)


def check_mesh(mesh, name):
    if len(mesh.faces) == 0 or not np.all(np.isfinite(mesh.vertices)):
        raise ValueError(f"{name}: empty or non-finite mesh")
    if mesh.faces.min() < 0 or mesh.faces.max() >= len(mesh.vertices):
        raise ValueError(f"{name}: face index out of range")
    a = mesh.vertices[mesh.faces[:, 1]] - mesh.vertices[mesh.faces[:, 0]]
    b = mesh.vertices[mesh.faces[:, 2]] - mesh.vertices[mesh.faces[:, 0]]
    if np.any(np.linalg.norm(np.cross(a, b), axis=1) <= 1e-12):
        raise ValueError(f"{name}: degenerate triangles")


def main():
    resolved = OUT_DIR.resolve()
    if resolved == UNITY_ROOT.resolve() or UNITY_ROOT.resolve() in resolved.parents:
        raise ValueError("candidate export must not write under the Unity tree")
    scene = read_scene(SOURCE)
    leaves = list(scene.leaves())
    if len(leaves) != EXPECTED_LEAVES:
        raise ValueError(f"expected {EXPECTED_LEAVES} leaves, found {len(leaves)}")
    grouped, labels, colors = {}, {}, {}
    for leaf in leaves:
        shape = scene.resolve(leaf.ref).shape()
        base = classify(leaf.label)
        mesh = to_unity(shape, HARDWARE_TESSELLATION if base.startswith("hardware") else (TOLERANCE, ANGULAR))
        check_mesh(mesh, leaf.label)
        c = shape.color
        key = "%02X%02X%02X" % tuple(int(round(max(0, min(1, x)) * 255)) for x in tuple(c)[:3]) if c else "none"
        g = f"{base}__{key}"
        grouped.setdefault(g, []).append(mesh)
        labels.setdefault(g, []).append(leaf.label)
    missing = [b for b in OUTPUTS if not any(k.split("__")[0] == b for k in grouped)]
    if missing:
        raise ValueError(f"empty groups: {missing}")
    merged = {}
    for g in sorted(grouped):
        m = trimesh.util.concatenate(grouped[g])
        m.merge_vertices()
        check_mesh(m, g)
        merged[g] = m
    asm = trimesh.util.concatenate(list(merged.values()))
    lo, hi = asm.bounds
    length = float(hi[2] - lo[2])
    if abs(length - 2 * EXPECTED_HALF_LENGTH_MM * MM) > 1e-3 or abs(lo[2] + hi[2]) > 1e-3:
        raise ValueError(f"envelope not centred/expected length: {lo[2]:.4f}..{hi[2]:.4f}")
    seam = STAGE_SEAM_X_MM * MM
    for g, m in merged.items():
        b = g.split("__")[0]
        if b in UPPER and m.bounds[0][2] < seam - 1e-4:
            raise ValueError(f"upper-stage group {g} extends aft of the stage seam")
        if b in BOOSTER and m.bounds[1][2] > seam + 1e-4:
            raise ValueError(f"booster group {g} extends forward of the stage seam")
    total = int(sum(len(m.faces) for m in merged.values()))
    if total > TRIANGLE_CEILING:
        raise ValueError(f"{total} triangles exceeds ceiling {TRIANGLE_CEILING}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"source": str(SOURCE.relative_to(HERE.parent.parent)),
              "sourceSha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "approvalState": "cad-approved-by-user; export candidate awaiting review",
              "toleranceMm": TOLERANCE, "axisMap": "Unity=(CAD.Y,CAD.Z,CAD.X)*0.001", "groups": {}}
    for old in OUT_DIR.glob("HalberdR26_*.obj"):
        old.unlink()
    for g in sorted(merged):
        base, key = g.split("__")
        name = OUTPUTS[base][:-4] + f"_{key}.obj"
        merged[g].export(OUT_DIR / name, file_type="obj")
        report["groups"][g] = {"file": name, "materialColorHex": "#" + key, "leaves": len(labels[g]),
                               "vertices": int(len(merged[g].vertices)), "triangles": int(len(merged[g].faces)),
                               "bounds": [[float(v) for v in r] for r in merged[g].bounds]}
    report["assembly"] = {"lengthM": length, "zRangeM": [float(lo[2]), float(hi[2])],
                          "maxRadialM": float(np.max(np.hypot(asm.vertices[:, 0], asm.vertices[:, 1]))),
                          "stageSeamZM": seam, "triangles": total, "triangleCeiling": TRIANGLE_CEILING}
    (OUT_DIR / "HalberdR26_Export_Report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"tolerance": TOLERANCE, "triangles": total, "length": length,
                      "maxRadial": report["assembly"]["maxRadialM"],
                      "materialSlots": len(report["groups"]), "groups": {g: v["triangles"] for g, v in report["groups"].items()}}, indent=1))


if __name__ == "__main__":
    main()
