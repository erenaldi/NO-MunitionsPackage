"""Export labeled Halberd CAD parts as deterministic Unity OBJ groups.

Candidate pass: output goes only to cad/candidates/halberd and never into the
production Unity Assets tree. All meshes are validated before any OBJ is written.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh
from cadgen import read_step

from generate_halberd_detailed import BODY_RADIUS, HALF_LENGTH, LENGTH, SEAM_X


SOURCE = Path(__file__).with_name("AAM-44_Halberd_Detailed.step")
OUTPUT_DIRECTORY = Path(__file__).parents[1] / "candidates" / "halberd"
REPORT_PATH = OUTPUT_DIRECTORY / "Halberd_Export_Report.json"
UNITY_ROOT = Path(__file__).parents[2] / "unity"

MILLIMETERS_TO_METERS = 0.001
TESSELLATION_TOLERANCE = 0.12
MAX_TRIANGLES = 75000
RADIAL_LIMIT_METERS = 0.219
STAGE_TOLERANCE = 0.0001
APPROVAL_STATE = "candidate-awaiting-review"

BODY = {"ramjet_body", "forward_body", "seeker_section", "radome"}
HARDWARE = {
    "stage_joint_band",
    "ramjet_joint_band",
    "forward_joint_band",
    "dorsal_launch_rail",
    "suspension_lug_1",
    "suspension_lug_2",
    "dorsal_wiring_conduit",
}
BOOSTER_BODY = {"booster_body", "booster_forward_collar", "booster_nozzle_outer"}
BOOSTER_NOZZLE = {"booster_nozzle_inner"}
BOOSTER_NOZZLE_RECESS = {"booster_nozzle_recess"}
INTAKES = {f"intake_{part}_{index}" for part in ("ramp", "lip", "duct") for index in (1, 2, 3)}
INTAKES.update(f"intake_cheek_{index}_{side}" for index in (1, 2, 3) for side in (1, 2))
SUSTAINER_FINS = {f"sustainer_fin_{index}" for index in (1, 2, 3)}
BOOSTER_FINS = {f"booster_fin_{index}" for index in (1, 2, 3)}
BOOSTER_FINS.update(f"booster_fin_root_{index}" for index in (1, 2, 3))

LABEL_GROUPS = {
    "body": BODY,
    "hardware": HARDWARE,
    "sustainer_nozzle": {"sustainer_nozzle"},
    "intakes": INTAKES,
    "sustainer_fins": SUSTAINER_FINS,
    "booster_body": BOOSTER_BODY,
    "booster_fins": BOOSTER_FINS,
    "booster_nozzle": BOOSTER_NOZZLE,
    "booster_nozzle_recess": BOOSTER_NOZZLE_RECESS,
}
EXPECTED_LABELS = frozenset().union(*LABEL_GROUPS.values())
UPPER_STAGE_GROUPS = {"body", "intakes", "sustainer_fins", "hardware", "sustainer_nozzle"}
BOOSTER_GROUPS = {"booster_body", "booster_fins", "booster_nozzle", "booster_nozzle_recess"}
OUTPUTS = {
    "body": "Halberd_Body.obj",
    "intakes": "Halberd_Intakes.obj",
    "sustainer_fins": "Halberd_SustainerFins.obj",
    "hardware": "Halberd_Hardware.obj",
    "sustainer_nozzle": "Halberd_SustainerNozzle.obj",
    "booster_body": "Halberd_BoosterBody.obj",
    "booster_fins": "Halberd_BoosterFins.obj",
    "booster_nozzle": "Halberd_BoosterNozzle.obj",
    "booster_nozzle_recess": "Halberd_BoosterNozzleRecess.obj",
}


def classify(label):
    matches = [group for group, labels in LABEL_GROUPS.items() if label in labels]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous Halberd label mapping: {label}: {matches}")
    if matches:
        return matches[0]
    raise ValueError(f"Unclassified Halberd CAD part: {label}")


def validate_labels(labels):
    """Map every label to exactly one group; reject duplicates, missing, unknown."""
    seen = set()
    mapping = {}
    for label in labels:
        if label in seen:
            raise ValueError(f"Duplicate Halberd part label: {label}")
        seen.add(label)
        mapping[label] = classify(label)
    missing = EXPECTED_LABELS - seen
    if missing:
        raise ValueError(f"Missing Halberd part labels: {sorted(missing)}")
    return mapping


def validate_mesh(mesh, label):
    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise ValueError(f"Halberd part '{label}' tessellated to an empty mesh")
    if not np.all(np.isfinite(mesh.vertices)):
        raise ValueError(f"Halberd part '{label}' has non-finite vertices")
    if mesh.faces.min() < 0 or mesh.faces.max() >= len(mesh.vertices):
        raise ValueError(f"Halberd part '{label}' has out-of-range face indices")
    edge_a = mesh.vertices[mesh.faces[:, 1]] - mesh.vertices[mesh.faces[:, 0]]
    edge_b = mesh.vertices[mesh.faces[:, 2]] - mesh.vertices[mesh.faces[:, 0]]
    areas = np.linalg.norm(np.cross(edge_a, edge_b), axis=1)
    if np.any(areas <= 1e-12):
        raise ValueError(f"Halberd part '{label}' has degenerate faces")


def validate_winding(mesh, group):
    if not mesh.is_winding_consistent:
        raise ValueError(f"Halberd group '{group}' has inconsistent winding; fix the CAD source")


def validate_stage_placement(grouped, seam):
    for group in UPPER_STAGE_GROUPS:
        if grouped[group].bounds[0][2] < seam - STAGE_TOLERANCE:
            raise ValueError(
                f"Halberd group '{group}' extends aft of the stage seam at {seam:.4f} m"
            )
    for group in BOOSTER_GROUPS:
        if grouped[group].bounds[1][2] > seam + STAGE_TOLERANCE:
            raise ValueError(
                f"Halberd group '{group}' extends forward of the stage seam at {seam:.4f} m"
            )


def validate_bounds(assembly, body, seam):
    length = float(assembly.bounds[1][2] - assembly.bounds[0][2])
    radial = np.linalg.norm(assembly.vertices[:, :2], axis=1)
    maximum_radius = float(radial.max())
    body_center = body.bounds.mean(axis=0)
    body_radius = float(np.linalg.norm(body.vertices[:, :2], axis=1).max())

    if abs(length - LENGTH * MILLIMETERS_TO_METERS) > 0.0001:
        raise ValueError(f"Converted length is {length:.6f} m")
    if abs(assembly.bounds[0][2] + HALF_LENGTH * MILLIMETERS_TO_METERS) > 0.0001:
        raise ValueError(f"Converted exhaust is at {assembly.bounds[0][2]:.6f} m")
    if abs(assembly.bounds[1][2] - HALF_LENGTH * MILLIMETERS_TO_METERS) > 0.0001:
        raise ValueError(f"Converted nose is at {assembly.bounds[1][2]:.6f} m")
    if abs(body_radius - BODY_RADIUS * MILLIMETERS_TO_METERS) > 0.0002:
        raise ValueError(f"Converted body radius is {body_radius:.6f} m")
    if np.linalg.norm(body_center[:2]) > 0.0001:
        raise ValueError(f"Converted body is off-axis: {body_center[:2].tolist()}")
    if abs(seam - SEAM_X * MILLIMETERS_TO_METERS) > 0.0001:
        raise ValueError(f"Converted booster seam is {seam:.6f} m")
    if maximum_radius > RADIAL_LIMIT_METERS + 1e-4:
        raise ValueError(
            f"Converted maximum radius is {maximum_radius:.6f} m; "
            f"baseline limit is {RADIAL_LIMIT_METERS} m"
        )
    return length, body_radius, maximum_radius


def to_unity_mesh(shape):
    vertices, triangles = shape.tessellate(TESSELLATION_TOLERANCE, 0.12)
    cad = np.array([(vertex.X, vertex.Y, vertex.Z) for vertex in vertices], dtype=float)
    game = np.column_stack((cad[:, 1], cad[:, 2], cad[:, 0]))
    game *= MILLIMETERS_TO_METERS
    return trimesh.Trimesh(vertices=game, faces=np.asarray(triangles), process=False)


def bounds_list(mesh):
    return [[float(value) for value in row] for row in mesh.bounds]


def assert_candidate_output(directory):
    unity = UNITY_ROOT.resolve()
    resolved = directory.resolve()
    if resolved == unity or unity in resolved.parents:
        raise ValueError(
            f"Candidate export must not write under {UNITY_ROOT}; "
            "production Unity assets are frozen this pass"
        )


def main():
    model = read_step(SOURCE)
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
            raise ValueError(f"Halberd mesh group is empty: {group}")
        mesh = trimesh.util.concatenate(grouped[group])
        mesh.merge_vertices()
        validate_mesh(mesh, group)
        validate_winding(mesh, group)
        grouped[group] = mesh
        combined.append(mesh)

    assembly = trimesh.util.concatenate(combined)
    body = grouped["body"]
    seam = float(grouped["booster_body"].bounds[1][2])
    length, body_radius, maximum_radius = validate_bounds(assembly, body, seam)
    validate_stage_placement(grouped, seam)
    total_triangles = int(sum(len(mesh.faces) for mesh in combined))
    if total_triangles > MAX_TRIANGLES:
        raise ValueError(f"Halberd export has {total_triangles} triangles; budget is {MAX_TRIANGLES}")

    assert_candidate_output(OUTPUT_DIRECTORY)
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
        "seamZ": seam,
        "center": [float(value) for value in assembly.bounds.mean(axis=0)],
        "triangles": total_triangles,
        "triangleBudget": MAX_TRIANGLES,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
