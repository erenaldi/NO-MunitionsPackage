"""Independently reload staged OBJ files and compare them with the export report."""
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

from export_halberd_unity_mesh import (
    OUTPUTS, REPORT_PATH, SOURCE, validate_bounds, validate_labels,
    validate_mesh, validate_stage_placement, validate_winding,
)


def main():
    report = json.loads(REPORT_PATH.read_text())
    assert report["sourceSha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert report["approvalState"] == "candidate-awaiting-review"
    assert set(report["groups"]) == set(OUTPUTS)
    meshes, labels = {}, []
    for group, record in report["groups"].items():
        path = Path(record["path"])
        assert path.resolve().parent == REPORT_PATH.resolve().parent
        mesh = trimesh.load_mesh(path, process=False)
        validate_mesh(mesh, group)
        validate_winding(mesh, group)
        assert len(mesh.faces) == record["triangles"]
        assert len(mesh.vertices) == record["vertices"]
        np.testing.assert_allclose(mesh.bounds, record["bounds"], atol=1e-8)
        labels.extend(record["labels"])
        meshes[group] = mesh
    mapping = validate_labels(labels)
    for group, record in report["groups"].items():
        assert all(mapping[label] == group for label in record["labels"])
    seam = meshes["booster_body"].bounds[1, 2]
    validate_stage_placement(meshes, seam)
    assembly = trimesh.util.concatenate(list(meshes.values()))
    validate_bounds(assembly, meshes["body"], seam)
    assert len(assembly.faces) == report["assembly"]["triangles"]
    assert len(assembly.faces) <= report["assembly"]["triangleBudget"]
    print(f"PASS: nine serialized OBJs reload with matching bounds, counts, winding, labels and source hash; {len(assembly.faces)} triangles.")


if __name__ == "__main__":
    main()
