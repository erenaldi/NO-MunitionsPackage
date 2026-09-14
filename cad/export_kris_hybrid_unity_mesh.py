"""Compatibility entry point for the authoritative Kris Unity exporter.

The current asset uses the MMR-S3 mesh length and grouped five-material
pipeline implemented by export_kris_unity_mesh.py.
"""

if __name__ == "__main__":
    from export_kris_unity_mesh import main as export_authoritative

    export_authoritative()
    raise SystemExit(0)

import json
from pathlib import Path

import numpy as np
import trimesh
from cadgen import read_step

SOURCE = Path(__file__).with_name("IRM-S4_Kris_PL10_Hybrid.step")
OUTPUT_DIRECTORY = (
    Path(__file__).parents[1]
    / "unity"
    / "BlueprinterEditor"
    / "Blueprinter-Editor"
    / "Assets"
    / "Blueprinter"
    / "Mods"
    / "KrisMod"
    / "Models"
)

SCALE = 0.65
TESSELLATION_TOLERANCE = 0.05
NOSE_Z = 2870.0
TVC_AFT_Z = -28.25
MIDPOINT_Z = (NOSE_Z + TVC_AFT_Z) / 2
BODY_RADIUS_MM = 72.5
LATTICE_TIP_RADIUS_MM = 225.637473
EXPECTED_PART_COUNT = 270

OUTPUTS = {
    "body": "KrisHybrid_Body.obj",
    "hardware": "KrisHybrid_Hardware.obj",
    "dark": "KrisHybrid_Dark.obj",
    "seeker": "KrisHybrid_Seeker.obj",
    "control_vanes": "KrisHybrid_ControlVanes.obj",
    "grid_fins": "KrisHybrid_GridFins.obj",
}


def classify(label):
    if label == "dark_nose_window":
        return "seeker"
    if label.startswith("tvc_static_vane_"):
        return "control_vanes"
    if label.startswith("kris_grid_fin_"):
        return "grid_fins"
    if label == "near_side_dark_panel" or label.startswith("paired_surface_mark_") or label in (
        "aft_round_panel_outline",
        "opposite_aft_round_panel_outline",
        "aft_dark_recess",
    ):
        return "dark"
    if label.startswith((
        "seeker_panel_border_",
        "seeker_base_collar",
        "seeker_collar_seam",
        "seeker_window_retaining_band",
        "nose_window_rim",
        "fine_section_joint_",
        "strake_attachment_",
        "front_fin_root_shoe_",
        "visible_fitting_",
        "front_section_seam_",
        "aft_end_cover",
        "aft_collar_edge_rim_",
        "grid_hinge_cover_",
        "grid_housing_fastener_",
        "tvc_exterior_mount_",
        "tvc_vane_mount_",
    )):
        return "hardware"
    if "fastener" in label or "_bolt_" in label or "_end_band" in label or "border" in label:
        return "hardware"
    if label.startswith((
        "body_section_",
        "rounded_nose_housing",
        "seeker_panel_",
        "central_strake_",
        "short_forward_blade_",
        "grid_fin_housing_",
        "grid_tvc_support_",
        "front_service_panel_",
        "quadrant_panel_",
        "aft_round_panel",
        "opposite_aft_round_panel",
        "aft_access_cover",
        "forward_access_cover",
    )) or label in ("longitudinal_surface_cover", "opposite_longitudinal_surface_cover"):
        return "body"
    raise ValueError(f"Unclassified hybrid part: {label}")


def to_unity_mesh(shape):
    vertices, triangles = shape.tessellate(TESSELLATION_TOLERANCE, 0.1)
    points = np.array([(v.X, v.Y, v.Z) for v in vertices], dtype=float)
    points[:, 2] -= MIDPOINT_Z
    points *= SCALE * 0.001
    return trimesh.Trimesh(vertices=points, faces=np.asarray(triangles), process=False)


def main():
    model = read_step(SOURCE)
    if len(model.children) != EXPECTED_PART_COUNT:
        raise ValueError(f"Expected {EXPECTED_PART_COUNT} hybrid parts, found {len(model.children)}")

    grouped = {name: [] for name in OUTPUTS}
    body_sections = []
    for child in model.children:
        mesh = to_unity_mesh(child)
        group = classify(child.label)
        grouped[group].append(mesh)
        if child.label.startswith("body_section_"):
            body_sections.append(mesh)
    empty = [name for name, meshes in grouped.items() if not meshes]
    if empty:
        raise ValueError(f"Hybrid mesh groups are empty: {empty}")

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
            "vertices": int(len(mesh.vertices)),
            "triangles": int(len(mesh.faces)),
            "bounds": mesh.bounds.tolist(),
        }

    assembly = trimesh.util.concatenate(combined)
    length = float(assembly.bounds[1][2] - assembly.bounds[0][2])
    grid_fins = trimesh.util.concatenate(grouped["grid_fins"])
    radial = float(np.linalg.norm(grid_fins.vertices[:, :2], axis=1).max())
    body = trimesh.util.concatenate(body_sections)
    body_radius = float(np.linalg.norm(body.vertices[:, :2], axis=1).max())
    center = assembly.bounds.mean(axis=0)
    expected_length = (NOSE_Z - TVC_AFT_Z) * 0.001 * SCALE
    expected_body_radius = BODY_RADIUS_MM * 0.001 * SCALE
    expected_lattice_radius = LATTICE_TIP_RADIUS_MM * 0.001 * SCALE
    if abs(length - expected_length) > 0.0002:
        raise ValueError(f"Converted length is {length:.6f} m; expected {expected_length:.6f}")
    if abs(body_radius - expected_body_radius) > 0.001:
        raise ValueError(f"Converted body radius is {body_radius:.6f} m; expected {expected_body_radius:.6f}")
    if abs(radial - expected_lattice_radius) > 0.002:
        raise ValueError(f"Converted lattice radius is {radial:.6f} m; expected {expected_lattice_radius:.6f}")
    if np.linalg.norm(center[:2]) > 0.0002:
        raise ValueError(f"Converted assembly is off-axis: {center[:2].tolist()}")

    report["assembly"] = {
        "length": length,
        "bodyRadius": body_radius,
        "latticeRadius": radial,
        "projectedSpan": float(np.abs(grid_fins.vertices[:, :2]).max() * 2),
        "center": center.tolist(),
        "effectsAnchorZ": float(TVC_AFT_Z - MIDPOINT_Z) * 0.001 * SCALE,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
