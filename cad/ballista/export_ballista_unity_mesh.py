"""Export AGM-110 Ballista CAD masters into Unity mesh groups.

Follows the Kris exporter pattern and docs/BALLISTA_UNITY_DELIVERY.md:
- CAD (X, Y, Z) mm maps to Unity (Y, Z, X) m (determinant +1, no reflection).
- The missile prefab uses the DEPLOYED master; the rack display uses the
  STOWED master.
- Wings export pivot-local: vertices are translated by the CAD pivot so the
  Unity child transform only carries the pivot position (no baked rotation on
  the node; poses come from the masters).
- Every label must classify through semantic_group() exactly once; groups may
  hold several material classes, exported as separate OBJ files that the Unity
  builder merges into submeshes.
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import trimesh
from cadgen import read_step

import ballista_geometry as bg

ROOT = Path(__file__).parent
OUTPUT_DIRECTORY = (
    Path(__file__).parents[2]
    / "unity"
    / "BlueprinterEditor"
    / "Blueprinter-Editor"
    / "Assets"
    / "Blueprinter"
    / "Mods"
    / "BallistaMod"
    / "Models"
)
REPORT = Path(__file__).with_name("Ballista_Export_Report.json")

from math import cos, radians, sin

MILLIMETERS_TO_METERS = 0.001
TESSELLATION_TOLERANCE = 0.12
TESSELLATION_ANGULAR_TOLERANCE = 0.12
TRIANGLE_BUDGET_PER_POSE = 75000
EXPECTED_PARTS_PER_POSE = 58
BOUNDS_TOLERANCE_METERS = 0.0005

MATERIAL_CLASSES = {
    "body": bg.BODY_COLOR,
    "panel": bg.PANEL_COLOR,
    "wing": bg.WING_COLOR,
    "hardware": bg.HARDWARE_COLOR,
    "edge": bg.EDGE_COLOR,
    "glass": bg.WINDOW_COLOR,
    "nozzle": bg.NOZZLE_COLOR,
    "recess": bg.RECESS_COLOR,
    "accent": bg.ACCENT_COLOR,
}
COLOR_TOLERANCE = 1e-5

MISSILE_PIVOTS = {
    -1: np.array([bg.WING_PIVOT_X, -bg.WING_PIVOT_Y, bg.WING_PIVOT_Z]),
    1: np.array([bg.WING_PIVOT_X, bg.WING_PIVOT_Y, bg.WING_PIVOT_Z]),
}

# Expected full-model bounds in Unity meters, derived from the same formulas
# check_ballista.py enforces (lateral constants are pre-scaled in the source;
# the blade's axial length is unscaled, so the sin term carries no scale).
DEPLOYED_SPAN_MM = 2 * (bg.WING_PIVOT_Y + bg.WING_LENGTH * sin(radians(bg.WING_ANGLE))
                        + (bg.WING_CHORD - 14 * bg.LATERAL_SCALE) / 2 * cos(radians(bg.WING_ANGLE)))
STOWED_SPAN_MM = 398.10111800802633 * bg.LATERAL_SCALE
EXPECTED_BOUNDS = {
    "missile": (DEPLOYED_SPAN_MM * MILLIMETERS_TO_METERS,
                STOWED_SPAN_MM * MILLIMETERS_TO_METERS,
                bg.LENGTH * MILLIMETERS_TO_METERS),
    "rack_display": (STOWED_SPAN_MM * MILLIMETERS_TO_METERS,
                     STOWED_SPAN_MM * MILLIMETERS_TO_METERS,
                     bg.LENGTH * MILLIMETERS_TO_METERS),
}

WING_GROUPS = {"wing_left", "wing_right"}


def classify_color(color):
    if color is None:
        raise ValueError("Ballista CAD part has no color")
    rgba = tuple(float(value) for value in color)
    for name, expected in MATERIAL_CLASSES.items():
        if max(abs(a - b) for a, b in zip(rgba, expected)) <= COLOR_TOLERANCE:
            return name
    raise ValueError(f"Unknown Ballista CAD color: {rgba}")


def classify_side(group, label):
    if group == "wing_left":
        return -1
    if group == "wing_right":
        return 1
    return 0


def to_unity_mesh(solid, pivot=None, label=""):
    vertices, triangles = solid.tessellate(
        TESSELLATION_TOLERANCE, TESSELLATION_ANGULAR_TOLERANCE)
    points = np.array([(v.X, v.Y, v.Z) for v in vertices], dtype=float)
    if pivot is not None:
        points -= pivot
    points = points[:, [1, 2, 0]] * MILLIMETERS_TO_METERS
    faces = np.asarray(triangles)
    edge_a = points[faces[:, 1]] - points[faces[:, 0]]
    edge_b = points[faces[:, 2]] - points[faces[:, 0]]
    faces = faces[np.linalg.norm(np.cross(edge_a, edge_b), axis=1) > 1e-12]
    mesh = trimesh.Trimesh(vertices=points, faces=faces, process=False)
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    if not mesh.is_watertight:
        raise ValueError(f"Open mesh after export: {label} ({len(mesh.faces)} faces)")
    mesh.fix_normals()
    return mesh


WING_PIVOT_UNITY = {
    -1: np.array([-bg.WING_PIVOT_Y, bg.WING_PIVOT_Z, bg.WING_PIVOT_X]) * MILLIMETERS_TO_METERS,
    1: np.array([bg.WING_PIVOT_Y, bg.WING_PIVOT_Z, bg.WING_PIVOT_X]) * MILLIMETERS_TO_METERS,
}


def collect_pose(step_path, pose_name):
    model = read_step(step_path)
    if len(model.children) != EXPECTED_PARTS_PER_POSE:
        raise ValueError(
            f"{pose_name}: expected {EXPECTED_PARTS_PER_POSE} parts, found {len(model.children)}")
    grouped = defaultdict(list)
    seen = set()
    for child in model.children:
        label = child.label
        if label in seen:
            raise ValueError(f"{pose_name}: duplicate label {label}")
        seen.add(label)
        group = bg.semantic_group(label)
        material = classify_color(child.color)
        pivot = None
        side = 0
        if group in WING_GROUPS:
            side = classify_side(group, label)
            pivot = MISSILE_PIVOTS[side]
        for solid in child.solids():
            grouped[(group, material)].append((to_unity_mesh(solid, pivot, label), side))
    return grouped


def export_pose(grouped, prefix, expected_bounds):
    output = {}
    total_triangles = 0
    group_files = defaultdict(list)
    placed = []
    for (group, material), entries in sorted(grouped.items()):
        if not entries:
            raise ValueError(f"Empty export group {group}/{material}")
        meshes = [entry[0] for entry in entries]
        mesh = trimesh.util.concatenate(meshes)
        file_name = f"{prefix}_{group}_{material}.obj"
        path = OUTPUT_DIRECTORY / file_name
        mesh.export(path, file_type="obj")
        triangles = int(len(mesh.faces))
        total_triangles += triangles
        group_files[group].append({"file": file_name, "material": material,
                                   "parts": len(meshes), "triangles": triangles,
                                   "bounds": mesh.bounds.tolist()})
        output[(group, material)] = mesh
        side = entries[0][1]
        if group in WING_GROUPS:
            placed.extend(m.copy() for m in meshes)
            for translated in placed[-len(meshes):]:
                translated.apply_translation(WING_PIVOT_UNITY[side])
        else:
            placed.extend(meshes)
    if total_triangles > TRIANGLE_BUDGET_PER_POSE:
        raise ValueError(f"{prefix}: {total_triangles} triangles exceeds budget")
    combined = trimesh.util.concatenate(placed)
    extents = (combined.bounds[1] - combined.bounds[0])
    for axis, expected in zip(range(3), expected_bounds):
        if abs(extents[axis] - expected) > BOUNDS_TOLERANCE_METERS:
            raise ValueError(
                f"{prefix}: axis {axis} extent {extents[axis]:.6f} != {expected:.6f}")
    report = {"groups": {group: files for group, files in sorted(group_files.items())},
              "triangles": total_triangles,
              "bounds": [extents.tolist(), combined.bounds[0].tolist(),
                         combined.bounds[1].tolist()]}
    return report


def main():
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    missile = collect_pose(ROOT / "AGM-110_Ballista_Deployed.step", "missile")
    rack = collect_pose(ROOT / "AGM-110_Ballista_Stowed.step", "rack")
    missile_report = export_pose(missile, "BallistaMissile",
                                 EXPECTED_BOUNDS["missile"])
    rack_report = export_pose(rack, "BallistaRack", EXPECTED_BOUNDS["rack_display"])
    report = {"missile": missile_report, "rack": rack_report}
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
