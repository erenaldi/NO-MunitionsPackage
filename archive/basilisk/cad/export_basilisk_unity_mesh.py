import json
from pathlib import Path

import numpy as np
import trimesh
from cadgen import read_step


SOURCE = Path(__file__).with_name("AAM41_Basilisk_Onshape_Finned.step")
OUTPUT_DIRECTORY = (
    Path(__file__).parents[1]
    / "unity"
    / "BlueprinterEditor"
    / "Blueprinter-Editor"
    / "Assets"
    / "Blueprinter"
    / "Mods"
    / "BasiliskMod"
    / "Models"
)

SOURCE_LENGTH_MM = 3400.0
TARGET_LENGTH = 2.9
SCALE = TARGET_LENGTH / SOURCE_LENGTH_MM
TESSELLATION_TOLERANCE = 0.0005

TAIL_FINS = {"Part 13", "Part 15", "Part 17", "Part 19"}
STRAKES = {"Part 14", "Part 16", "Part 18", "Part 20"}
SEEKER = {"seeker_neck", "identification_band", "seeker_body", "ir_seeker_dome"}
OUTPUTS = {
    "body": "Basilisk_Body.obj",
    "seeker": "Basilisk_Seeker.obj",
    "strakes": "Basilisk_Strakes.obj",
    "tail_fins": "Basilisk_TailFins.obj",
}


def classify(label):
    if label in TAIL_FINS:
        return "tail_fins"
    if label in STRAKES:
        return "strakes"
    if label in SEEKER:
        return "seeker"
    return "body"


def to_unity_mesh(shape):
    vertices, triangles = shape.tessellate(TESSELLATION_TOLERANCE, 0.1)
    points = np.array([(vertex.X, -vertex.Z, vertex.Y) for vertex in vertices], dtype=float)
    points *= SCALE
    points[:, 2] -= TARGET_LENGTH * 0.5
    return trimesh.Trimesh(vertices=points, faces=np.asarray(triangles), process=False)


def main():
    model = read_step(SOURCE)
    if len(model.children) != 20:
        raise ValueError(f"Expected 20 Onshape parts, found {len(model.children)}")

    labels = {child.label for child in model.children}
    missing = (TAIL_FINS | STRAKES | SEEKER) - labels
    if missing:
        raise ValueError(f"Missing expected Onshape parts: {sorted(missing)}")

    grouped = {name: [] for name in OUTPUTS}
    for child in model.children:
        grouped[classify(child.label)].append(to_unity_mesh(child))

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    report = {}
    for group, file_name in OUTPUTS.items():
        mesh = trimesh.util.concatenate(grouped[group])
        mesh.merge_vertices()
        mesh.fix_normals()
        output = OUTPUT_DIRECTORY / file_name
        mesh.export(output, file_type="obj")
        report[group] = {
            "path": str(output),
            "vertices": int(len(mesh.vertices)),
            "triangles": int(len(mesh.faces)),
            "bounds": mesh.bounds.tolist(),
        }

    all_meshes = trimesh.util.concatenate([mesh for meshes in grouped.values() for mesh in meshes])
    length = float(all_meshes.bounds[1][2] - all_meshes.bounds[0][2])
    if abs(length - TARGET_LENGTH) > 0.001:
        raise ValueError(f"Converted length is {length:.6f} m; expected {TARGET_LENGTH:.6f} m")
    report["overallLength"] = length
    report["scale"] = SCALE
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
