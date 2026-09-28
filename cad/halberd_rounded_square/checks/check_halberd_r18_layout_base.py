"""Saved-artifact verification for the R18 annotation-only presentation base."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cadgen import build123d as bd, read_scene
from cadgen.geometry import boundary_edges, self_intersections, topology_errors
from halberd_r16_shapes import FASTENERS, MAIN_LABEL, fastener_seat, joint_pocket


R12 = "halberd_r12"
R16 = "halberd_r16"
R18 = "halberd_r18_layout_base"
REMOVED_PREFIX = "main_service_"
CLOCKS = (0.0, 90.0, 180.0, 270.0)
RESTORATION_CENTER = (-320.0, 0.0, 0.0)
RESTORATION_SIZE = (200.0, 400.0, 400.0)
REPORT_PATH = ROOT / "reviews" / "halberd_r18_layout_base_checks.json"


def load(name):
    scene = read_scene(ROOT / "STEP" / f"{name}.step")
    leaves = tuple(scene.leaves())
    parts = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in leaves}
    assert len(parts) == len(leaves), f"{name}: duplicate saved labels"
    return scene, parts, leaves


def volume(shape):
    return shape.volume if shape else 0.0


def identical(actual, expected, tolerance=0.05):
    assert volume(actual - expected) < tolerance, "missing volume in geometry comparison"
    assert volume(expected - actual) < tolerance, "unexpected volume in geometry comparison"


def color_tuple(shape):
    return tuple(shape.color)


def bounds(shape):
    box = shape.bounding_box()
    return {
        "min_mm": [box.min.X, box.min.Y, box.min.Z],
        "max_mm": [box.max.X, box.max.Y, box.max.Z],
        "size_mm": [box.size.X, box.size.Y, box.size.Z],
    }


def appearance_by_label(scene, sidecar):
    by_ref = sidecar["appearance"]["assignments"]
    return {leaf.label: by_ref[leaf.ref.lstrip("#")]
            for leaf in scene.leaves() if leaf.ref.lstrip("#") in by_ref}


def material_signature(sidecar, material_id):
    material = sidecar["appearance"]["materials"][material_id]
    return tuple((key, material.get(key)) for key in
                 ("name", "roughness", "metalness", "color", "baseColor"))


def expected_main(r12_main):
    # This is intentionally independent of the source's masked restoration delta.
    result = r12_main - joint_pocket()
    for clock in CLOCKS:
        result = result - fastener_seat(clock)
    result.label = MAIN_LABEL
    return result


def preflight():
    r16_scene, r16, _ = load(R16)
    r12_scene, r12, _ = load(R12)
    r18_scene, r18, _ = load(R18)
    assert len(r16) == 44 and len(r12) == 27
    assert len(r18) == 28
    expected_labels = {label for label in r16 if not label.startswith(REMOVED_PREFIX)}
    assert set(r18) == expected_labels
    assert len([label for label in r16 if label.startswith(REMOVED_PREFIX)]) == 16
    assert all(not label.startswith(REMOVED_PREFIX) for label in r18)

    clip = bd.Box(*RESTORATION_SIZE).translate(RESTORATION_CENTER)
    delta = (r12[MAIN_LABEL] - r16[MAIN_LABEL]) & clip
    assert delta.volume > 0.0, "restoration mask produced no old seat-cut restoration"
    assert volume(delta - clip) < 0.05, "restoration escaped the bounded mask"
    expected = expected_main(r12[MAIN_LABEL])
    identical(r18[MAIN_LABEL], expected)

    r16_box = bounds(r16_scene.roots[0].shape())
    r18_box = bounds(r18_scene.roots[0].shape())
    assert abs(r18_box["size_mm"][0] - 3370.0) < 0.01, r18_box
    assert all(abs(a - b) < 0.01 for a, b in zip(r16_box["size_mm"][1:],
                                                  r18_box["size_mm"][1:])), \
        ("baseline transverse widths changed", r16_box, r18_box)
    print(json.dumps({
        "preflight": "PASS",
        "parts": len(r18),
        "restoration_delta_volume_mm3": delta.volume,
        "bbox_mm": r18_box,
        "baseline_transverse_sizes_mm": r16_box["size_mm"][1:],
        "independent_main_comparison": "PASS",
    }, indent=2))


def run_full():
    r12_scene, r12, _ = load(R12)
    r16_scene, r16, _ = load(R16)
    r18_scene, r18, leaves = load(R18)
    r16_sidecar = json.loads((ROOT / "STEP" / f"{R16}.step.json").read_text())
    r18_sidecar = json.loads((ROOT / "STEP" / f"{R18}.step.json").read_text())

    assert r18_sidecar["documentHash"] == r18_scene.document_hash, "stale R18 sidecar hash"
    assert len(leaves) == len(r18) == 28
    expected_labels = {label for label in r16 if not label.startswith(REMOVED_PREFIX)}
    assert set(r18) == expected_labels
    removed_labels = {label for label in r16 if label.startswith(REMOVED_PREFIX)}
    assert len(removed_labels) == 16
    assert not (removed_labels & set(r18))
    assert set(r18) - {MAIN_LABEL} == set(r16) - removed_labels - {MAIN_LABEL}

    for label in sorted(set(r18) - {MAIN_LABEL}):
        identical(r18[label], r16[label])
        assert color_tuple(r18[label]) == color_tuple(r16[label]), (label, "color changed")

    main = r18[MAIN_LABEL]
    assert color_tuple(main) == color_tuple(r16[MAIN_LABEL]), "main-body color changed"
    independent = expected_main(r12[MAIN_LABEL])
    identical(main, independent)
    assert volume(main - r12[MAIN_LABEL]) < 0.05, "R18 main gained volume beyond R12"

    clip = bd.Box(*RESTORATION_SIZE).translate(RESTORATION_CENTER)
    restoration = (r12[MAIN_LABEL] - r16[MAIN_LABEL]) & clip
    assert restoration.volume > 0.0
    expected_restored = r16[MAIN_LABEL] + restoration
    identical(main, expected_restored)
    assert volume(restoration - clip) < 0.05, "restoration lies outside its specified mask"

    r16_box = bounds(r16_scene.roots[0].shape())
    r18_box = bounds(r18_scene.roots[0].shape())
    assert abs(r18_box["size_mm"][0] - 3370.0) < 0.01, r18_box
    assert all(abs(a - b) < 0.01 for a, b in zip(r16_box["size_mm"][1:],
                                                  r18_box["size_mm"][1:])), \
        ("baseline transverse widths changed", r16_box, r18_box)

    print(f"Checking 28 saved placements for native solid validity and self-intersection",
          flush=True)
    for index, leaf in enumerate(leaves, 1):
        shape = r18[leaf.label]
        solids = shape.solids()
        assert len(solids) == 1, (leaf.label, "expected one native solid", len(solids))
        assert solids[0].volume > 0.0, (leaf.label, "non-positive solid volume")
        assert shape.is_valid, (leaf.label, "invalid native shape")
        assert not topology_errors(shape), (leaf.label, "topology errors")
        assert all(not boundary_edges(shell) for shell in shape.shells()), \
            (leaf.label, "open shell")
        assert not self_intersections(shape), (leaf.label, "self-intersection")
        if index % 7 == 0 or index == len(leaves):
            print(f"  {index}/{len(leaves)} placements", flush=True)

    r16_appearance = appearance_by_label(r16_scene, r16_sidecar)
    r18_appearance = appearance_by_label(r18_scene, r18_sidecar)
    expected_appearance = {label: material for label, material in r16_appearance.items()
                           if label not in removed_labels}
    assert set(r18_appearance) == set(expected_appearance), \
        "retained material assignment labels changed"
    for label, old_id in expected_appearance.items():
        new_id = r18_appearance[label]
        assert material_signature(r18_sidecar, new_id) == material_signature(r16_sidecar, old_id), \
            (label, "resolved finish changed", old_id, new_id)
    assert material_signature(r18_sidecar, r18_appearance["main_joint_liner_1"])[0][1] == \
        "Small metallic hardware"
    for label in ("main_nozzle_dark_recess", "main_nozzle_dark_floor",
                  "booster_nozzle_dark_recess", "booster_nozzle_dark_floor"):
        if label in r18_appearance:
            assert material_signature(r18_sidecar, r18_appearance[label]) == \
                material_signature(r16_sidecar, r16_appearance[label]), label

    report = {
        "ok": True,
        "status": "PASS",
        "source_step": str(ROOT / "STEP" / f"{R18}.step"),
        "source_hash": r18_scene.document_hash,
        "R12_hash": r12_scene.document_hash,
        "R16_hash": r16_scene.document_hash,
        "parts": len(r18),
        "removed_main_service_labels": sorted(removed_labels),
        "preserved_nonbody_parts_exact": len(set(r18) - {MAIN_LABEL}),
        "main_equals_R12_minus_R16_joint_cuts": True,
        "restoration_mask_delta_volume_mm3": restoration.volume,
        "bbox_mm": r18_box,
        "baseline_bbox_mm": r16_box,
        "native_solid_checks": {
            "single_positive_valid_closed_solid_per_part": len(leaves),
            "topology_errors": 0,
            "self_intersections": 0,
        },
        "materials_sidecar_hash_valid": True,
        "retained_material_assignments": len(r18_appearance),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("PASS: R18 saved-geometry and material-sidecar checks")


if __name__ == "__main__":
    if "--preflight" in sys.argv:
        preflight()
    else:
        run_full()
