"""Export the approved R5 Phantom STEPs as deterministic Unity OBJ groups.

Two candidate states, each from its own approved R5 master:

- deployed:  RDM-9_Phantom_R5_Dart.step          (flight state)
- retracted: RDM-9_Phantom_R5_Dart_Retracted.step (rack display state)

R6 and any other source are rejected inputs. Output goes to the Phantom
candidate asset root (Assets/Blueprinter/Mods/PhantomMod/Models) with a
manifest beside it. All meshes are validated before any OBJ is written.
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from cadgen import read_step


OUTPUT_DIRECTORY = (
    Path(__file__).parents[2]
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
# Derived-engine-mesh correction for the issue-005 aft-face z-fighting defect:
# the approved R5 CAD has the nozzle_lip aft face coplanar with the smooth_body
# aft cap, which renders as alternating radial flicker/faceting. The exporter
# recesses the lip forward (CAD +x, Unity +z) by this amount so the nozzle
# reads visibly recessed inside the body aft rim without a proud lip. The
# approved STEP geometry is never modified.
NOZZLE_RECESS_METERS = 0.003

STATES = {
    "deployed": {
        "source": "RDM-9_Phantom_R5_Dart.step",
        "model_label": "RDM-9_Phantom_R5_Dart",
        "groups": {
            "body": ("smooth_body",),
            "wings": ("wing_port", "wing_starboard"),
            "fins": ("tail_fin_port", "tail_fin_starboard", "dorsal_fin", "ventral_fin"),
            "nozzle": ("nozzle_lip", "nozzle_recess"),
        },
        "outputs": {
            "body": "Phantom_Body.obj",
            "wings": "Phantom_Wings.obj",
            "fins": "Phantom_Fins.obj",
            "nozzle": "Phantom_Nozzle.obj",
        },
        "maximum_span": MAXIMUM_SPAN_METERS,
        "carriage_radius": None,
    },
    "retracted": {
        "source": "RDM-9_Phantom_R5_Dart_Retracted.step",
        "model_label": "RDM-9_Phantom_R5_Dart_Retracted",
        "groups": {
            "body": ("smooth_body",),
            "wings": ("stowed_wing_stack",),
            "fins": ("tail_fin_port", "tail_fin_starboard", "dorsal_fin", "ventral_fin"),
            "nozzle": ("nozzle_lip", "nozzle_recess"),
            "fairing": ("hinge_fairing",),
        },
        "outputs": {
            "body": "Phantom_Retracted_Body.obj",
            "wings": "Phantom_Retracted_Wings.obj",
            "fins": "Phantom_Retracted_Fins.obj",
            "nozzle": "Phantom_Retracted_Nozzle.obj",
            "fairing": "Phantom_Retracted_Fairing.obj",
        },
        "maximum_span": 0.247,
        "carriage_radius": 0.125,
    },
}

# Backward-compatible deployed-state aliases used by the helper tests.
SOURCE = Path(__file__).with_name(STATES["deployed"]["source"])
MODEL_LABEL = STATES["deployed"]["model_label"]
LABEL_GROUPS = {name: set(labels) for name, labels in STATES["deployed"]["groups"].items()}
EXPECTED_LABELS = frozenset().union(*LABEL_GROUPS.values())
OUTPUTS = dict(STATES["deployed"]["outputs"])


def validate_source(path, state="deployed"):
    expected = STATES[state]["source"]
    if Path(path).name != expected:
        raise ValueError(
            f"Phantom exporter accepts only {expected} for {state}; got {Path(path).name}"
        )


def classify(label, state="deployed"):
    groups = STATES[state]["groups"]
    matches = [group for group, labels in groups.items() if label in labels]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous Phantom label mapping: {label}: {matches}")
    if matches:
        return matches[0]
    raise ValueError(f"Unclassified Phantom CAD part: {label}")


def validate_labels(labels, state="deployed"):
    """Map every label to exactly one group; reject duplicates, missing, unknown."""
    expected = frozenset().union(*STATES[state]["groups"].values())
    seen = set()
    mapping = {}
    for label in labels:
        if label in seen:
            raise ValueError(f"Duplicate Phantom part label: {label}")
        seen.add(label)
        mapping[label] = classify(label, state)
    missing = expected - seen
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


def validate_bounds(assembly, body, state="deployed"):
    spec = STATES[state]
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
    if span > spec["maximum_span"] + 0.001:
        raise ValueError(
            f"Converted maximum span is {span:.6f} m; expected {spec['maximum_span']} m"
        )
    if spec["carriage_radius"] is not None and maximum_radius > spec["carriage_radius"] + 0.001:
        raise ValueError(
            f"Converted maximum radius is {maximum_radius:.6f} m; exceeds the "
            f"{spec['carriage_radius']} m carriage envelope"
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


def recess_nozzle_lip(mesh):
    """Translate the nozzle lip forward (Unity +z) so its aft face is no
    longer coplanar with the body aft cap. Translation preserves topology,
    winding, and watertightness, so no export validation is weakened."""
    mesh.apply_translation((0.0, 0.0, NOZZLE_RECESS_METERS))
    return mesh


def validate_nozzle_recess(body_mesh, lip_mesh):
    """The derived nozzle lip must sit recessed inside the body aft face:
    its aft plane must be forward of the body aft plane by at least the
    recess amount, and it must never protrude past the body aft plane."""
    body_aft = float(body_mesh.bounds[0][2])
    lip_aft = float(lip_mesh.bounds[0][2])
    if lip_aft < body_aft - 1e-6:
        raise ValueError(
            f"Phantom nozzle lip stands proud of the body aft face: {lip_aft:.6f} m"
        )
    if lip_aft - body_aft < NOZZLE_RECESS_METERS - 1e-6:
        raise ValueError(
            f"Phantom nozzle lip is not recessed from the body aft face: "
            f"lip aft {lip_aft:.6f} m vs body aft {body_aft:.6f} m"
        )
    return lip_aft - body_aft


def main(state="deployed", output_directory=None, report_path=None):
    if state not in STATES:
        raise ValueError(f"Unknown Phantom state: {state}")
    spec = STATES[state]
    source = Path(__file__).with_name(spec["source"])
    validate_source(source, state)
    model = read_step(source)
    if model.label != spec["model_label"]:
        raise ValueError(
            f"Phantom exporter accepts only {spec['model_label']} for {state}; got {model.label}"
        )
    mapping = validate_labels([child.label for child in model.children], state)

    output_directory = output_directory or OUTPUT_DIRECTORY
    report_path = report_path or REPORT_PATH
    outputs = spec["outputs"]
    grouped = {name: [] for name in outputs}
    part_labels = {name: [] for name in outputs}
    body_mesh = None
    lip_mesh = None
    for child in model.children:
        group = mapping[child.label]
        mesh = to_unity_mesh(child)
        validate_mesh(mesh, child.label)
        if child.label == "smooth_body":
            body_mesh = mesh
        if child.label == "nozzle_lip":
            recess_nozzle_lip(mesh)
            lip_mesh = mesh
        grouped[group].append(mesh)
        part_labels[group].append(child.label)
    validate_nozzle_recess(body_mesh, lip_mesh)

    combined = []
    for group in outputs:
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
    length, body_radius, maximum_radius, span = validate_bounds(assembly, body, state)
    total_triangles = validate_groups(grouped)

    output_directory.mkdir(parents=True, exist_ok=True)
    state_report = {
        "source": str(source),
        "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "approvalState": APPROVAL_STATE,
        "groups": {},
    }
    for group, file_name in outputs.items():
        mesh = grouped[group]
        output = output_directory / file_name
        mesh.export(output, file_type="obj")
        state_report["groups"][group] = {
            "path": str(output),
            "labels": part_labels[group],
            "vertices": int(len(mesh.vertices)),
            "triangles": int(len(mesh.faces)),
            "bounds": bounds_list(mesh),
        }

    state_report["assembly"] = {
        "length": length,
        "bodyRadius": body_radius,
        "maximumRadius": maximum_radius,
        "maximumSpan": span,
        "carriageEnvelopeRadius": spec["carriage_radius"],
        "center": [float(value) for value in assembly.bounds.mean(axis=0)],
        "triangles": total_triangles,
        "triangleBudget": MAX_TRIANGLES,
    }

    report = {"states": {}}
    if report_path.exists():
        existing = json.loads(report_path.read_text(encoding="ascii"))
        report["states"] = existing.get("states", {})
    report["states"][state] = state_report
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps(state_report, indent=2))
    return report


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "deployed")