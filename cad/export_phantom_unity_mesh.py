"""Export the approved R5 Phantom deployed STEP as deterministic Unity OBJ groups.

Deployed-only candidate pass: accepts only RDM-9_Phantom_R5_Dart.step. R6 and the
retracted state are rejected inputs. Output goes to the Phantom candidate asset
root (Assets/Blueprinter/Mods/PhantomMod/Models) with a manifest beside it. All
meshes are validated before any OBJ is written.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh
from cadgen import read_step


SOURCE = Path(__file__).with_name("RDM-9_Phantom_R5_Dart.step")
MODEL_LABEL = "RDM-9_Phantom_R5_Dart"
OUTPUT_DIRECTORY = (
    Path(__file__).parents[1]
    / "unity"
    / "BlueprinterEditor"
    / "Blueprinter-Editor"
    / "Assets"
    / "Blueprinter"
    / "Mods"
    / "PhantomMod"
    / "Models"
)
REPORT_PATH = OUTPUT_DIRECTORY.parent / "Phantom_Export_Report.json"

MILLIMETERS_TO_METERS = 0.001
TESSELLATION_TOLERANCE = 0.12
MAX_TRIANGLES = 75000
LENGTH_METERS = 2800.0 * MILLIMETERS_TO_METERS
BODY_RADIUS_METERS = 0.1002
MAXIMUM_SPAN_METERS = 1.3987
BOUNDS_TOLERANCE = 0.001
APPROVAL_STATE = "candidate-awaiting-review"

BODY = {"smooth_body"}
WINGS = {"wing_port", "wing_starboard"}
FINS = {"tail_fin_port", "tail_fin_starboard", "dorsal_fin", "ventral_fin"}
NOZZLE = {"nozzle_lip", "nozzle_recess"}

LABEL_GROUPS = {
    "body": BODY,
    "wings": WINGS,
    "fins": FINS,
    "nozzle": NOZZLE,
}
EXPECTED_LABELS = frozenset().union(*LABEL_GROUPS.values())
OUTPUTS = {
    "body": "Phantom_Body.obj",
    "wings": "Phantom_Wings.obj",
    "fins": "Phantom_Fins.obj",
    "nozzle": "Phantom_Nozzle.obj",
}


def validate_source(path):
    if Path(path).name != SOURCE.name:
        raise ValueError(
            f"Phantom exporter accepts only {SOURCE.name}; got {Path(path).name}"
        )


def classify(label):
    matches = [group for group, labels in LABEL_GROUPS.items() if label in labels]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous Phantom label mapping: {label}: {matches}")
    if matches:
        return matches[0]
    raise ValueError(f"Unclassified Phantom CAD part: {label}")


def validate_labels(labels):
    """Map every label to exactly one group; reject duplicates, missing, unknown."""
    seen = set()
    mapping = {}
    for label in labels:
        if label in seen:
            raise ValueError(f"Duplicate Phantom part label: {label}")
        seen.add(label)
        mapping[label] = classify(label)
    missing = EXPECTED_LABELS - seen
    if missing:
        raise ValueError(f"Missing Phantom part labels: {sorted(missing)}")
    return mapping


def validate_mesh(mesh, label):
    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise ValueError(f"Phantom part '{label}' tessellated to an empty mesh")
    if not np.all(np.isfinite(mesh.vertices)):
        raise ValueError(f"Phantom part '{label}' has non-finite vertices")
    if mesh.faces.min() < 0 or mesh.faces.max() >= len(mesh.vertices):
        raise ValueError(f"Phantom part '{label}' has out-of-range face indices")
    edge_a = mesh.vertices[mesh.faces[:, 1]] - mesh.vertices[mesh.faces[:, 0]]
    edge_b = mesh.vertices[mesh.faces[:, 2]] - mesh.vertices[mesh.faces[:, 0]]
    areas = np.linalg.norm(np.cross(edge_a, edge_b), axis=1)
    if np.any(areas <= 1e-12):
        raise ValueError(f"Phantom part '{label}' has degenerate faces")


def validate_winding(mesh, group):
    if not mesh.is_winding_consistent:
        raise ValueError(f"Phantom group '{group}' has inconsistent winding; fix the CAD source")


def validate_bounds(assembly, body):
    length = float(assembly.bounds[1][2] - assembly.bounds[0][2])
    radial = np.linalg.norm(assembly.vertices[:, :2], axis=1)
    maximum_radius = float(radial.max())
    body_radius = float(np.linalg.norm(body.vertices[:, :2], axis=1).max())
    center = assembly.bounds.mean(axis=0)
    span = float(
        max(
            assembly.bounds[1][0] - assembly.bounds[0][0],
            assembly.bounds[1][1] - assembly.bounds[0][1],
        )
    )

    if abs(length - LENGTH_METERS) > BOUNDS_TOLERANCE:
        raise ValueError(f"Converted length is {length:.6f} m")
    if abs(assembly.bounds[0][2] + LENGTH_METERS * 0.5) > BOUNDS_TOLERANCE:
        raise ValueError(f"Converted tail is not at {-LENGTH_METERS * 0.5:.6f} m")
    if abs(assembly.bounds[1][2] - LENGTH_METERS * 0.5) > BOUNDS_TOLERANCE:
        raise ValueError(f"Converted nose is not at {LENGTH_METERS * 0.5:.6f} m")
    if abs(body_radius - BODY_RADIUS_METERS) > 0.001:
        raise ValueError(f"Converted body radius is {body_radius:.6f} m")
    if np.linalg.norm(center[:2]) > 0.001:
        raise ValueError(f"Converted assembly is off-axis: {center[:2].tolist()}")
    if span > MAXIMUM_SPAN_METERS + 0.001:
        raise ValueError(
            f"Converted maximum span is {span:.6f} m; expected {MAXIMUM_SPAN_METERS} m"
        )
    return length, body_radius, maximum_radius, span


def validate_groups(grouped):
    total = 0
    for group, mesh in grouped.items():
        if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            raise ValueError(f"Phantom mesh group is empty: {group}")
        if not mesh.is_watertight:
            raise ValueError(f"Phantom mesh group is not watertight: {group}")
        total += len(mesh.faces)
    if total > MAX_TRIANGLES:
        raise ValueError(f"Phantom export has {total} triangles; budget is {MAX_TRIANGLES}")
    return total


def to_unity_mesh(shape):
    vertices, triangles = shape.tessellate(TESSELLATION_TOLERANCE, 0.12)
    cad = np.array([(vertex.X, vertex.Y, vertex.Z) for vertex in vertices], dtype=float)
    game = np.column_stack((cad[:, 1], cad[:, 2], cad[:, 0]))
    game *= MILLIMETERS_TO_METERS
    faces = np.asarray(triangles)
    # The sharp apex vertex tessellates to one zero-area face (two coincident
    # apex corners); drop it like the Kris exporter does.
    edge_a = game[faces[:, 1]] - game[faces[:, 0]]
    edge_b = game[faces[:, 2]] - game[faces[:, 0]]
    faces = faces[np.linalg.norm(np.cross(edge_a, edge_b), axis=1) > 1e-12]
    return trimesh.Trimesh(vertices=game, faces=faces, process=False)


def bounds_list(mesh):
    return [[float(value) for value in row] for row in mesh.bounds]


def main():
    validate_source(SOURCE)
    model = read_step(SOURCE)
    if model.label != MODEL_LABEL:
        raise ValueError(f"Phantom exporter accepts only {MODEL_LABEL}; got {model.label}")
    mapping = validate_labels([child.label for child in model.children])

    grouped = {name: [] for name in OUTPUTS}
    part_labels = {name: [] for name in OUTPUTS}
    for child in model.children:
        group = mapping[child.label]
        mesh = to_unity_mesh(child)
        validate_mesh(mesh, child.label)
        grouped[group].append(mesh)
        part_labels[group].append(child.label)

    combined = []
    for group in OUTPUTS:
        if not grouped[group]:
            raise ValueError(f"Phantom mesh group is empty: {group}")
        mesh = trimesh.util.concatenate(grouped[group])
        mesh.merge_vertices()
        validate_mesh(mesh, group)
        validate_winding(mesh, group)
        grouped[group] = mesh
        combined.append(mesh)

    assembly = trimesh.util.concatenate(combined)
    body = grouped["body"]
    length, body_radius, maximum_radius, span = validate_bounds(assembly, body)
    total_triangles = validate_groups(grouped)

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    report = {
        "source": str(SOURCE),
        "sourceSha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "approvalState": APPROVAL_STATE,
        "groups": {},
    }
    for group, file_name in OUTPUTS.items():
        mesh = grouped[group]
        output = OUTPUT_DIRECTORY / file_name
        mesh.export(output, file_type="obj")
        report["groups"][group] = {
            "path": str(output),
            "labels": part_labels[group],
            "vertices": int(len(mesh.vertices)),
            "triangles": int(len(mesh.faces)),
            "bounds": bounds_list(mesh),
        }

    report["assembly"] = {
        "length": length,
        "bodyRadius": body_radius,
        "maximumRadius": maximum_radius,
        "maximumSpan": span,
        "center": [float(value) for value in assembly.bounds.mean(axis=0)],
        "triangles": total_triangles,
        "triangleBudget": MAX_TRIANGLES,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()