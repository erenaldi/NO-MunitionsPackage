import json
from pathlib import Path

import numpy as np
import trimesh
from cadgen import read_step


SOURCE = Path(__file__).with_name("IRM-S4_Kris_PL10_Hybrid.step")
REPORT = Path(__file__).with_name("Kris_Hybrid_Export_Report.json")
OUTPUT_DIRECTORY = (
    Path(__file__).parents[2]
    / "unity"
    / "BlueprinterEditor"
    / "Blueprinter-Editor"
    / "Assets"
    / "Blueprinter"
    / "Mods"
    / "KrisMod"
    / "Models"
)

EXPECTED_PARTS = 270
EXPECTED_TRIANGLES = 100328
TARGET_LENGTH_METERS = 2.8715922
SOURCE_BODY_DIAMETER_MM = 145.0
MILLIMETERS_TO_METERS = 0.001
TESSELLATION_TOLERANCE = 0.05
COLOR_TOLERANCE = 1e-5

# STEP preserves the CAD colors as linear RGBA values. Keeping one mesh per
# palette entry lets Unity reproduce every modeled panel and fastener without
# depending on OBJ material import behavior.
PALETTE = {
    "body": (0.630757, 0.630757, 0.584078, 1.0),
    "hardware": (0.270498, 0.309469, 0.309469, 1.0),
    "dark": (0.033105, 0.039546, 0.042311, 1.0),
    "grid_fins": (0.018500, 0.023153, 0.026241, 1.0),
    "seeker": (0.008568, 0.019382, 0.026241, 1.0),
}
OUTPUTS = {
    "body": "Kris_Body.obj",
    "hardware": "Kris_Hardware.obj",
    "dark": "Kris_Dark.obj",
    "grid_fins": "Kris_GridFins.obj",
    "seeker": "Kris_Seeker.obj",
}


def classify_color(color):
    if color is None:
        raise ValueError("Kris CAD part has no color")
    rgba = tuple(float(value) for value in color)
    for group, expected in PALETTE.items():
        if max(abs(actual - target) for actual, target in zip(rgba, expected)) <= COLOR_TOLERANCE:
            return group
    raise ValueError(f"Unknown Kris CAD color: {rgba}")


def to_unity_mesh(shape, scale, axial_center_mm):
    vertices, triangles = shape.tessellate(TESSELLATION_TOLERANCE, 0.1)
    points = np.array([(vertex.X, vertex.Y, vertex.Z) for vertex in vertices], dtype=float)
    points[:, 2] -= axial_center_mm
    points *= MILLIMETERS_TO_METERS * scale
    faces = np.asarray(triangles)
    edge_a = points[faces[:, 1]] - points[faces[:, 0]]
    edge_b = points[faces[:, 2]] - points[faces[:, 0]]
    faces = faces[np.linalg.norm(np.cross(edge_a, edge_b), axis=1) > 1e-12]
    return trimesh.Trimesh(vertices=points, faces=faces, process=False)


def main():
    model = read_step(SOURCE)
    if len(model.children) != EXPECTED_PARTS:
        raise ValueError(f"Expected {EXPECTED_PARTS} hybrid parts, found {len(model.children)}")

    bounds = model.bounding_box()
    source_length_mm = bounds.max.Z - bounds.min.Z
    scale = TARGET_LENGTH_METERS / (source_length_mm * MILLIMETERS_TO_METERS)
    axial_center_mm = (bounds.min.Z + bounds.max.Z) * 0.5

    grouped = {name: [] for name in OUTPUTS}
    grouped_labels = {name: [] for name in OUTPUTS}
    body_sections = []
    for child in model.children:
        group = classify_color(child.color)
        mesh = to_unity_mesh(child, scale, axial_center_mm)
        grouped[group].append(mesh)
        grouped_labels[group].append(child.label)
        if child.label.startswith("body_section_"):
            body_sections.append(mesh)

    empty = [name for name, meshes in grouped.items() if not meshes]
    if empty:
        raise ValueError(f"Kris mesh groups are empty: {empty}")
    if sum(len(meshes) for meshes in grouped.values()) != EXPECTED_PARTS:
        raise ValueError("Not every Kris CAD part was assigned to an export mesh")
    if not body_sections:
        raise ValueError("Kris export found no cylindrical body sections")

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    report = {}
    combined = []
    for group, file_name in OUTPUTS.items():
        mesh = trimesh.util.concatenate(grouped[group])
        mesh.merge_vertices()
        mesh.fix_normals()
        output = OUTPUT_DIRECTORY / file_name
        mesh.export(output, file_type="obj")
        combined.append(mesh)
        report[group] = {
            "path": str(output),
            "parts": len(grouped[group]),
            "labels": grouped_labels[group],
            "vertices": int(len(mesh.vertices)),
            "triangles": int(len(mesh.faces)),
            "bounds": mesh.bounds.tolist(),
        }

    assembly = trimesh.util.concatenate(combined)
    body = trimesh.util.concatenate(body_sections)
    length = float(assembly.bounds[1][2] - assembly.bounds[0][2])
    body_radius = float(np.linalg.norm(body.vertices[:, :2], axis=1).max())
    deployed_radius = float(np.linalg.norm(assembly.vertices[:, :2], axis=1).max())
    center = assembly.bounds.mean(axis=0)
    expected_body_radius = SOURCE_BODY_DIAMETER_MM * 0.5 * MILLIMETERS_TO_METERS * scale

    if abs(length - TARGET_LENGTH_METERS) > 0.0001:
        raise ValueError(f"Converted length is {length:.6f} m")
    if abs(body_radius - expected_body_radius) > 0.0001:
        raise ValueError(
            f"Converted body radius is {body_radius:.6f} m; expected {expected_body_radius:.6f} m"
        )
    if abs(assembly.bounds[0][2] + TARGET_LENGTH_METERS * 0.5) > 0.0001:
        raise ValueError(f"Converted tail is not at {-TARGET_LENGTH_METERS * 0.5:.6f} m")
    if abs(assembly.bounds[1][2] - TARGET_LENGTH_METERS * 0.5) > 0.0001:
        raise ValueError(f"Converted nose is not at {TARGET_LENGTH_METERS * 0.5:.6f} m")
    if np.linalg.norm(center[:2]) > 0.0001:
        raise ValueError(f"Converted assembly is off-axis: {center[:2].tolist()}")
    if len(assembly.faces) != EXPECTED_TRIANGLES:
        raise ValueError(
            f"Converted assembly has {len(assembly.faces)} triangles; expected {EXPECTED_TRIANGLES}"
        )

    report["assembly"] = {
        "source": str(SOURCE),
        "parts": EXPECTED_PARTS,
        "length": length,
        "bodyRadius": body_radius,
        "bodyDiameter": body_radius * 2,
        "deployedRadius": deployed_radius,
        "maximumSpan": max(
            float(assembly.bounds[1][0] - assembly.bounds[0][0]),
            float(assembly.bounds[1][1] - assembly.bounds[0][1]),
        ),
        "visualScale": scale,
        "center": center.tolist(),
        "bounds": assembly.bounds.tolist(),
        "vertices": int(len(assembly.vertices)),
        "triangles": int(len(assembly.faces)),
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
