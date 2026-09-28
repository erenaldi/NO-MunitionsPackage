"""R17 full-detail saved-artifact checker.

Independent verification of the six saved R17 STEP scenes against the saved
R16 baseline and the R17 layout contract.  The builder's ``build_components``
supplies the expected per-host cutters, owners and prototypes; every fact
below is measured on the saved artifacts, never on a rebuilt model.

Scenes (555 saved placements):
  halberd_r17 (246), halberd_r17_separated (246), halberd_r17_focus (25),
  halberd_r17_main_fin_focus (7), halberd_r17_booster_fin_focus (7),
  halberd_r17_nozzle_focus (24).
"""
from __future__ import annotations

import json
import math
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cadgen import build123d as bd, read_scene, srgb
from cadgen.geometry import boundary_edges, self_intersections, topology_errors
from halberd_r17_shapes import (
    ACCESS_CLOCKS,
    BOOSTER_ACCESS_STATIONS,
    BOOSTER_BODY,
    BODY_FOCUS_LABELS,
    BOOSTER_FIN_FOCUS_LABELS,
    FIN_CLOCKS,
    MAIN_ACCESS_STATIONS,
    MAIN_BODY,
    MAIN_FIN_FOCUS_LABELS,
    NOZZLE_FOCUS_LABELS,
    SEAM_ROWS,
    SEPARATION,
    build_components,
)
from halberd_r17_interface_shapes import (
    FASTENER_HEAD_TOP_RADIUS,
    FASTENER_TOP_RECESS,
    FIN_INSET_DEPTH,
    FIN_PATCH_DEPTH,
)

REPORT_PATH = ROOT / "reviews" / "halberd_r17_checks.json"
LAYOUT_PATH = ROOT / "reviews" / "halberd_r17_layout.json"
VOLUME_TOLERANCE = 0.01
IDENTITY_TOLERANCE = 0.05
COLOR_TOLERANCE = 1e-6
BBOX_EPSILON = 1e-6

SCENES = {
    "halberd_r17": 246,
    "halberd_r17_separated": 246,
    "halberd_r17_focus": 25,
    "halberd_r17_main_fin_focus": 7,
    "halberd_r17_booster_fin_focus": 7,
    "halberd_r17_nozzle_focus": 24,
}

# Expected R17 material definitions (name/roughness/metalness/baseColor).
EXPECTED_R17_MATERIALS = {
    "r17_service_paint": {"name": "R17 access cover paint", "roughness": 0.65,
                          "metalness": 0.15, "baseColor": "#B5BDC3"},
    "r17_service_border": {"name": "R17 recessed access border", "roughness": 0.9,
                           "metalness": 0.05, "baseColor": "#505960"},
    "r17_detail_metal": {"name": "R17 small metallic hardware", "roughness": 0.38,
                         "metalness": 0.65, "baseColor": "#87939B"},
    "r17_inset": {"name": "R17 fin-root inset", "roughness": 0.65,
                  "metalness": 0.15, "baseColor": "#A7B0B7"},
}
MATERIAL_COLOR = {
    "r17_service_paint": "#B5BDC3",
    "r17_service_border": "#505960",
    "r17_detail_metal": "#87939B",
    "r17_inset": "#A7B0B7",
}
FAMILY_MATERIAL = {
    "service_cover": "r17_service_paint",
    "service_border": "r17_service_border",
    "service_fastener": "r17_detail_metal",
    "seam_liner": "r17_detail_metal",
    "seam_fastener": "r17_detail_metal",
    "fin_strip": "r17_inset",
    "fin_fastener": "r17_detail_metal",
    "nozzle": "r17_detail_metal",
}


def volume(shape):
    return shape.volume if shape else 0.0


def identical(actual, expected, tolerance=IDENTITY_TOLERANCE):
    assert volume(actual - expected) < tolerance, "unexpected/missing comparison geometry"
    assert volume(expected - actual) < tolerance, "comparison is missing expected geometry"


def color_close(actual, expected, tolerance=COLOR_TOLERANCE):
    assert len(actual) == len(expected) and all(abs(a - b) < tolerance
                                                 for a, b in zip(actual, expected)), \
        (actual, expected, tolerance)


def boxes_overlap(aa, bb, eps=BBOX_EPSILON):
    """Conservative bbox overlap; coplanar faces within eps count as touching."""
    return not (aa.max.X < bb.min.X - eps or bb.max.X < aa.min.X - eps or
                aa.max.Y < bb.min.Y - eps or bb.max.Y < aa.min.Y - eps or
                aa.max.Z < bb.min.Z - eps or bb.max.Z < aa.min.Z - eps)


def common_face_areas(a, b):
    a_faces = list(a.faces())
    b_faces = list(b.faces())
    a_boxes = [face.bounding_box() for face in a_faces]
    b_boxes = [face.bounding_box() for face in b_faces]
    areas = []
    for index, face_a in enumerate(a_faces):
        box_a = a_boxes[index]
        for other, face_b in enumerate(b_faces):
            if not boxes_overlap(box_a, b_boxes[other]):
                continue
            common = face_a & face_b
            if common and common.area > 0.001:
                areas.append(common.area)
    return areas


def load(name):
    scene = read_scene(ROOT / "STEP" / f"{name}.step")
    leaves = tuple(scene.leaves())
    parts = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in leaves}
    assert len(parts) == len(leaves), f"duplicate labels in {name}"
    return scene, parts


def load_sidecar(name):
    return json.loads((ROOT / "STEP" / f"{name}.step.json").read_text())


def validate_placements(name, expected_count):
    """Every saved placement: one positive solid, closed, no topology/self-intersection."""
    scene, parts = load(name)
    rows = []
    leaves = tuple(scene.leaves())
    print(f"Checking {name}: {len(leaves)} saved placements", flush=True)
    for index, leaf in enumerate(leaves, 1):
        shape = parts[leaf.label]
        solids = shape.solids()
        assert len(solids) == 1, (name, leaf.label, "expected one solid")
        assert solids[0].volume > 0.0, (name, leaf.label, "non-positive solid")
        assert not topology_errors(shape), (name, leaf.label, "topology errors")
        assert all(not boundary_edges(shell) for shell in shape.shells()), \
            (name, leaf.label, "open shell")
        assert not self_intersections(shape), (name, leaf.label, "self-intersection")
        rows.append({"label": leaf.label, "ref": leaf.ref,
                     "volume_mm3": solids[0].volume})
        if index % 25 == 0 or index == len(leaves):
            print(f"  {name}: {index}/{len(leaves)} ({leaf.label})", flush=True)
    assert len(rows) == expected_count, (name, len(rows), expected_count)
    return scene, parts, rows


def appearance_by_label(scene, sidecar):
    refs = sidecar["appearance"]["assignments"]
    result = {}
    for leaf in scene.leaves():
        ref = leaf.ref.lstrip("#")
        if ref in refs:
            result[leaf.label] = refs[ref]
    return result


def resolved_material(sidecar, material_id):
    return sidecar["appearance"]["materials"][material_id]


def material_core(material):
    """The semantic material properties shared across sidecar revisions."""
    return {key: material[key] for key in ("name", "roughness", "metalness")
            if key in material}


def check_materials(scene, parts, sidecar, expected_core_by_label, color_by_label):
    """Sidecar hash, per-label resolved material definitions and saved colors.

    Material ids may be normalized between sidecar revisions (``local/``
    prefix), so the resolved definition's semantic properties are compared.
    """
    assert sidecar["documentHash"] == scene.document_hash, "stale material sidecar"
    assignments = appearance_by_label(scene, sidecar)
    assert set(assignments) == set(expected_core_by_label), \
        (sorted(set(assignments) ^ set(expected_core_by_label)))
    for label, expected_core in expected_core_by_label.items():
        material = resolved_material(sidecar, assignments[label])
        assert material_core(material) == expected_core, (label, material)
    for label, hex_color in color_by_label.items():
        color_close(tuple(parts[label].color), tuple(srgb(hex_color)))
    return len(assignments)


def run_full():
    REPORT_PATH.write_text(json.dumps({"ok": False, "status": "Checks incomplete"}) + "\n")
    layout = json.loads(LAYOUT_PATH.read_text())
    assert layout["status"] == "R17_GATE2_BUILT_CHECKER_PENDING", layout["status"]

    # ---- Builder-supplied expectations (verified against saved artifacts below).
    components = build_components()
    baseline_parts = components["baseline_parts"]
    saved_baseline = components["saved_baseline_parts"]
    prototypes = components["prototypes"]
    cutters_by_host = components["cutters_by_host"]
    new_parts = components["new_parts"]
    detail_owner = components["detail_owner"]
    detail_family = components["detail_family"]
    family_counts = components["family_counts"]
    changed_hosts = set(components["host_after_by_label"])
    unchanged_labels = sorted(set(baseline_parts) - changed_hosts)
    new_labels = [part.label for part in new_parts]
    assert len(new_labels) == 202 and len(set(new_labels)) == 202
    assert len(changed_hosts) == 10 and len(unchanged_labels) == 34
    assert set(unchanged_labels) == set(layout["unchanged_baseline_labels"])
    assert set(changed_hosts) == set(layout["changed_hosts"])
    assert set(new_labels) == {entry["label"] for entry in layout["new_parts"]}

    # ---- Saved R16 baseline identity (pilot host selection source).
    baseline_scene = read_scene(ROOT / "STEP" / "halberd_r16.step")
    assert baseline_scene.document_hash == layout["baseline_document_hash"], \
        "saved R16 baseline changed since the layout manifest"
    assert baseline_scene.document_hash == components["baseline_scene"].document_hash

    # ---- 1. Every saved placement in all six scenes.
    scenes = {}
    for name, expected_count in SCENES.items():
        scene, parts, rows = validate_placements(name, expected_count)
        scenes[name] = {"scene": scene, "parts": parts, "rows": rows}
    full_scene = scenes["halberd_r17"]["scene"]
    full = scenes["halberd_r17"]["parts"]
    separated = scenes["halberd_r17_separated"]["parts"]
    focus = scenes["halberd_r17_focus"]["parts"]
    main_fin_focus = scenes["halberd_r17_main_fin_focus"]["parts"]
    booster_fin_focus = scenes["halberd_r17_booster_fin_focus"]["parts"]
    nozzle_focus = scenes["halberd_r17_nozzle_focus"]["parts"]
    placements_validated = sum(len(scenes[name]["rows"]) for name in SCENES)
    assert placements_validated == 555

    # ---- 2. Label sets.
    assert set(full) == set(baseline_parts) | set(new_labels)
    assert set(separated) == set(full)
    assert set(focus) == set(BODY_FOCUS_LABELS)
    assert set(main_fin_focus) == set(MAIN_FIN_FOCUS_LABELS)
    assert set(booster_fin_focus) == set(BOOSTER_FIN_FOCUS_LABELS)
    assert set(nozzle_focus) == set(NOZZLE_FOCUS_LABELS)
    assert len(full) == len(separated) == 246
    assert len(focus) == 25 and len(main_fin_focus) == 7
    assert len(booster_fin_focus) == 7 and len(nozzle_focus) == 24

    # ---- 3. Materials and colors in every state.
    r16_sidecar = load_sidecar("halberd_r16")
    r16_assignments = appearance_by_label(baseline_scene, r16_sidecar)
    r16_materials = r16_sidecar["appearance"]["materials"]
    full_sidecar = load_sidecar("halberd_r17")
    for shared in sorted(set(r16_materials) & set(full_sidecar["appearance"]["materials"])):
        assert material_core(r16_materials[shared]) == material_core(
            full_sidecar["appearance"]["materials"][shared]), shared

    expected_core_by_label = {}
    color_by_label = {}
    for label in baseline_parts:
        if label in r16_assignments:
            expected_core_by_label[label] = material_core(
                r16_materials[r16_assignments[label]])
    for label in new_labels:
        material_id = FAMILY_MATERIAL[detail_family[label]]
        expected_core_by_label[label] = material_core(
            EXPECTED_R17_MATERIALS[material_id])
        color_by_label[label] = MATERIAL_COLOR[material_id]
    no_assignment_labels = set(baseline_parts) - set(r16_assignments)
    assert no_assignment_labels == changed_hosts | {"main_ogive"}, no_assignment_labels

    separated_sidecar = load_sidecar("halberd_r17_separated")
    check_materials(full_scene, full, full_sidecar, expected_core_by_label,
                    color_by_label)
    check_materials(scenes["halberd_r17_separated"]["scene"], separated,
                    separated_sidecar, expected_core_by_label, color_by_label)
    focus_material_counts = {}
    for name, labels in (("halberd_r17_focus", BODY_FOCUS_LABELS),
                         ("halberd_r17_main_fin_focus", MAIN_FIN_FOCUS_LABELS),
                         ("halberd_r17_booster_fin_focus", BOOSTER_FIN_FOCUS_LABELS),
                         ("halberd_r17_nozzle_focus", NOZZLE_FOCUS_LABELS)):
        sidecar = load_sidecar(name)
        expected = {label: expected_core_by_label[label] for label in labels
                    if label in expected_core_by_label}
        colors = {label: color_by_label[label] for label in labels
                  if label in color_by_label}
        focus_material_counts[name] = check_materials(
            scenes[name]["scene"], scenes[name]["parts"], sidecar, expected, colors)

    # Baseline colors preserved on every unchanged and changed host.
    for label in baseline_parts:
        color_close(tuple(full[label].color), tuple(saved_baseline[label].color))

    # ---- 4. Full/separated rigid correspondence (booster -340 X, main fixed).
    for label, shape in full.items():
        if label.startswith("booster"):
            identical(separated[label], shape.moved(bd.Location((-SEPARATION, 0.0, 0.0))))
        else:
            identical(separated[label], shape)
        color_close(tuple(separated[label].color), tuple(shape.color))

    # ---- 5. The 34 unchanged R16 parts are exact (geometry + color).
    for label in unchanged_labels:
        identical(full[label], saved_baseline[label])
        color_close(tuple(full[label].color), tuple(saved_baseline[label].color))
        restored = separated[label].moved(bd.Location((SEPARATION, 0.0, 0.0))) \
            if label.startswith("booster") else separated[label]
        identical(restored, saved_baseline[label])

    # ---- 6. The 10 changed hosts equal original minus the exact planned cutters.
    host_cuts = {}
    for host_label, cutters in cutters_by_host.items():
        original = saved_baseline[host_label]
        tool = bd.Compound(children=cutters, label=f"{host_label}_r17_cutters")
        expected = original - tool
        identical(full[host_label], expected)
        gained = volume(full[host_label] - original)
        removed = volume(original - full[host_label])
        assert gained < VOLUME_TOLERANCE, (host_label, "host gained volume", gained)
        assert removed > 0.0, (host_label, "cutters removed no volume")
        assert len(full[host_label].solids()) == 1
        host_cuts[host_label] = {
            "cutter_count": len(cutters),
            "removed_volume_mm3": removed,
            "gained_volume_mm3": gained,
            "cutter_labels": [cutter.label for cutter in cutters],
        }

    # ---- 7. All 202 new details: inside old host skin, zero owner overlap,
    #          supporting common face area > 0.
    support = {}
    for authored_part in new_parts:
        label = authored_part.label
        part = full[label]
        identical(part, authored_part)
        owner = detail_owner[label]
        old_host = saved_baseline[owner]
        cut_host = full[owner]
        assert volume(part - old_host) < VOLUME_TOLERANCE, \
            (label, "outside old host skin", volume(part - old_host))
        overlap = volume(part & cut_host)
        assert overlap < VOLUME_TOLERANCE, (label, "owner overlap", overlap)
        distance = part.distance_to(cut_host)
        assert distance < 1e-4, (label, "no support contact", distance)
        areas = common_face_areas(part, cut_host)
        common_area = max(areas, default=0.0)
        assert common_area > 0.001, (label, "missing common support face", areas)
        support[label] = {"owner_host": owner, "family": detail_family[label],
                          "distance_mm": distance, "overlap_mm3": overlap,
                          "common_face_area_mm2": common_area}
        print(f"  support {label} on {owner}: {common_area:.3f} mm2", flush=True)

    # ---- 8. Pair interference with cached conservative bboxes.
    new_boxes = {label: full[label].bounding_box() for label in new_labels}
    baseline_boxes = {label: saved_baseline[label].bounding_box()
                      for label in baseline_parts}
    detail_pair_candidates = 0
    detail_pair_overlaps = []
    for first, second in combinations(new_labels, 2):
        if not boxes_overlap(new_boxes[first], new_boxes[second]):
            continue
        detail_pair_candidates += 1
        overlap = volume(full[first] & full[second])
        if overlap >= VOLUME_TOLERANCE:
            detail_pair_overlaps.append((first, second, overlap))
    assert not detail_pair_overlaps, detail_pair_overlaps[:5]

    nonowner_candidates = 0
    nonowner_overlaps = []
    for label in new_labels:
        owner = detail_owner[label]
        for other_label, other_box in baseline_boxes.items():
            if other_label == owner:
                continue
            if not boxes_overlap(new_boxes[label], other_box):
                continue
            nonowner_candidates += 1
            overlap = volume(full[label] & saved_baseline[other_label])
            if overlap >= VOLUME_TOLERANCE:
                nonowner_overlaps.append((label, other_label, overlap))
    assert not nonowner_overlaps, nonowner_overlaps[:5]

    # ---- 9. Exact fourfold cover/fin copies and eightfold nozzle fasteners.
    fourfold = {}
    for stage, stations in (
        ("main", MAIN_ACCESS_STATIONS),
        ("booster", BOOSTER_ACCESS_STATIONS),
    ):
        for x_center, length, width in stations:
            row = f"xm{abs(int(x_center))}" if x_center < 0 else f"xp{int(x_center)}"
            for part_name in ("cover", "border", "screw_1", "screw_2"):
                base = full[f"{stage}_access_{row}_000_{part_name}"]
                for clock in ACCESS_CLOCKS[1:]:
                    copy = full[f"{stage}_access_{row}_{int(clock):03d}_{part_name}"]
                    identical(copy, base.rotate(bd.Axis.X, -clock))
                    fourfold[f"{stage}_access_{row}_{part_name}_{int(clock):03d}"] = True
    for stage, prefix in (("main", "main_r17_fin"),
                          ("booster", "booster_r17_fin_fairing")):
        for occurrence, clock in enumerate(FIN_CLOCKS, 1):
            if occurrence == 1:
                continue
            for part_name in (["inset_strip"] +
                              [f"fastener_{i}" for i in range(1, 5)]):
                base = full[f"{prefix}_1_{part_name}"]
                copy = full[f"{prefix}_{occurrence}_{part_name}"]
                identical(copy, base.rotate(bd.Axis.X, -clock))
                fourfold[f"{prefix}_{occurrence}_{part_name}"] = True
    for stage in ("main", "booster"):
        base = full[f"{stage}_r17_nozzle_fastener_1"]
        for index in range(2, 9):
            copy = full[f"{stage}_r17_nozzle_fastener_{index}"]
            identical(copy, base.rotate(bd.Axis.X, -45.0 * (index - 1)))
            fourfold[f"{stage}_r17_nozzle_fastener_{index}"] = True

    # ---- 10. Seam dimensions/heights and all 16 seam heads visible through skin.
    seam_checks = {}
    for x_center in SEAM_ROWS:
        row = f"xm{abs(int(x_center))}" if x_center < 0 else f"xp{int(x_center)}"
        for clock in ACCESS_CLOCKS:
            group = f"main_seam_{row}_{int(clock):03d}"
            liner = full[f"{group}_liner"].rotate(bd.Axis.X, clock)
            screw = full[f"{group}_screw"].rotate(bd.Axis.X, clock)
            liner_box = liner.bounding_box()
            screw_box = screw.bounding_box()
            assert abs(liner_box.min.X - (x_center - 0.55)) < 0.01, (group, liner_box)
            assert abs(liner_box.max.X - (x_center + 0.55)) < 0.01, (group, liner_box)
            assert abs(liner_box.min.Y + 24.9) < 0.01, (group, liner_box)
            assert abs(liner_box.max.Y - 24.9) < 0.01, (group, liner_box)
            assert abs(liner_box.min.Z - 99.4) < 0.01, (group, liner_box)
            assert abs(liner_box.max.Z - 99.8) < 0.01, (group, liner_box)
            assert abs(screw_box.min.X - (x_center - 7.0 - 1.78)) < 0.01, (group, screw_box)
            assert abs(screw_box.max.X - (x_center - 7.0 + 1.78)) < 0.01, (group, screw_box)
            assert abs(screw_box.min.Z - 98.5) < 0.01, (group, screw_box)
            assert abs(screw_box.max.Z - 99.65) < 0.01, (group, screw_box)
            site_x = x_center - 7.0
            p_body = _rotate_point((site_x, 0.0, 98.4), -clock)
            p_air = _rotate_point((site_x, 0.0, 99.9), -clock)
            assert full[MAIN_BODY].is_inside(p_body), (group, "body missing under seat")
            assert not full[MAIN_BODY].is_inside(p_air), (group, "head enclosed under skin")
            seam_checks[group] = {
                "liner_bounds_mm": [liner_box.min.X, liner_box.min.Y, liner_box.min.Z,
                                    liner_box.max.X, liner_box.max.Y, liner_box.max.Z],
                "screw_bounds_mm": [screw_box.min.X, screw_box.min.Y, screw_box.min.Z,
                                    screw_box.max.X, screw_box.max.Y, screw_box.max.Z],
                "body_at_98_4_mm": True, "air_at_99_9_mm": True,
            }

    # ---- 11. Slot presence on every fastener head (120 heads).
    slot_checks = {}
    for stage, stations in (
        ("main", MAIN_ACCESS_STATIONS),
        ("booster", BOOSTER_ACCESS_STATIONS),
    ):
        for x_center, length, width in stations:
            row = f"xm{abs(int(x_center))}" if x_center < 0 else f"xp{int(x_center)}"
            screw_offset = length / 2.0 - 12.0
            for clock in ACCESS_CLOCKS:
                group = f"{stage}_access_{row}_{int(clock):03d}"
                for index, sign in enumerate((-1, 1), 1):
                    site_x = x_center + sign * screw_offset
                    screw = full[f"{group}_screw_{index}"].rotate(bd.Axis.X, clock)
                    assert not screw.is_inside((site_x, 0.0, 99.65)), \
                        (group, index, "slot is filled")
                    assert screw.is_inside((site_x + 0.45, 0.0, 99.5)), \
                        (group, index, "head material missing")
                    slot_checks[f"{group}_screw_{index}"] = True
    for x_center in SEAM_ROWS:
        row = f"xm{abs(int(x_center))}" if x_center < 0 else f"xp{int(x_center)}"
        for clock in ACCESS_CLOCKS:
            group = f"main_seam_{row}_{int(clock):03d}"
            screw = full[f"{group}_screw"].rotate(bd.Axis.X, clock)
            site_x = x_center - 7.0
            assert not screw.is_inside((site_x, 0.0, 99.65)), (group, "slot is filled")
            assert screw.is_inside((site_x + 0.45, 0.0, 99.5)), (group, "head material missing")
            slot_checks[f"{group}_screw"] = True
    for stage, prototype_key, prefix in (
        ("main", "main_fin", "main_r17_fin"),
        ("booster", "booster_fin", "booster_r17_fin_fairing"),
    ):
        proto = prototypes[prototype_key]
        for occurrence, clock in enumerate(FIN_CLOCKS, 1):
            for index, site in enumerate(proto.parameters["screw_sites"], 1):
                point = bd.Vector(site["point_mm"])
                normal = bd.Vector(site["outward_normal"]).normalized()
                slot_probe = _rotate_point(
                    (point - normal * (FASTENER_TOP_RECESS + 0.10)), -clock)
                head_probe = _rotate_point((point - normal * 0.72), -clock)
                fastener = full[f"{prefix}_{occurrence}_fastener_{index}"]
                assert not fastener.is_inside(slot_probe), \
                    (prefix, occurrence, index, "slot is filled")
                assert fastener.is_inside(head_probe), \
                    (prefix, occurrence, index, "head material missing")
                slot_checks[f"{prefix}_{occurrence}_fastener_{index}"] = True
    for stage, proto_key in (("main", "main_nozzle"), ("booster", "booster_nozzle")):
        proto = prototypes[proto_key]
        for index, site in enumerate(proto.parameters["screw_sites"], 1):
            point = bd.Vector(site["center_mm"])
            normal = bd.Vector((-1.0, 0.0, 0.0))
            slot_probe = point - normal * (FASTENER_TOP_RECESS + 0.10)
            head_probe = point - normal * 0.72
            fastener = full[f"{stage}_r17_nozzle_fastener_{index}"]
            assert not fastener.is_inside(slot_probe), (stage, index, "slot is filled")
            assert fastener.is_inside(head_probe), (stage, index, "head material missing")
            slot_checks[f"{stage}_r17_nozzle_fastener_{index}"] = True
    assert len(slot_checks) == 120

    # ---- 12. Nozzle ring recess and open-bore preservation.
    nozzle_checks = {}
    for stage, mouth_x, cavity_radius, screw_radius in (
        ("main", -1123.3333333333, 65.0, 91.5),
        ("booster", -1685.0, 69.0, 78.4),
    ):
        host = full[MAIN_BODY if stage == "main" else BOOSTER_BODY]
        ring = full[f"{stage}_r17_nozzle_ring"]
        ring_box = ring.bounding_box()
        assert abs(ring_box.min.X - (mouth_x + FIN_INSET_DEPTH)) < 0.01, (stage, ring_box)
        assert abs(ring_box.max.X - (mouth_x + FIN_PATCH_DEPTH)) < 0.01, (stage, ring_box)
        assert abs(ring_box.max.Y - 72.75) < 0.01, (stage, ring_box)
        assert abs(ring_box.max.Z - 72.75) < 0.01, (stage, ring_box)
        mid_x = mouth_x + (FIN_INSET_DEPTH + FIN_PATCH_DEPTH) / 2.0
        assert ring.is_inside((mid_x, 0.0, 71.5)), (stage, "ring annulus missing")
        assert not ring.is_inside((mid_x, 0.0, 69.0)), (stage, "ring occludes bore")
        assert not ring.is_inside((mid_x, 0.0, 74.0)), (stage, "ring exceeds recess")
        bore_open = []
        for clock in range(0, 360, 45):
            angle = math.radians(clock)
            probe = (mouth_x + 0.1, (cavity_radius - 1.0) * math.sin(angle),
                     (cavity_radius - 1.0) * math.cos(angle))
            assert not host.is_inside(probe), (stage, clock, "mouth bore occluded")
            bore_open.append(clock)
        head_clearance = screw_radius - FASTENER_HEAD_TOP_RADIUS - cavity_radius
        assert head_clearance > 0.5, (stage, head_clearance)
        nozzle_checks[stage] = {
            "ring_bounds_mm": [ring_box.min.X, ring_box.min.Y, ring_box.min.Z,
                               ring_box.max.X, ring_box.max.Y, ring_box.max.Z],
            "bore_open_clocks_degrees": bore_open,
            "head_to_bore_radial_mm": head_clearance,
        }

    # ---- 13. Four open intake channels.
    intake_checks = {}
    for i in range(1, 5):
        floor = full[f"main_intake_dark_floor_{i}"]
        back = max(vertex.X for vertex in floor.vertices())
        channel_shapes = [full[MAIN_BODY], full[f"main_intake_dark_recess_{i}"], floor]
        blocked = []
        for x in (back + 0.1, -300.0, -100.0, 100.0, 400.0, 560.0):
            angle = math.radians(45.0 + 90.0 * (i - 1))
            point = (x, 120.0 * math.sin(angle), 120.0 * math.cos(angle))
            if any(shape.solids()[0].is_inside(point) for shape in channel_shapes):
                blocked.append(x)
        assert not blocked, (i, blocked)
        intake_checks[i] = {"back_x_mm": back, "blocked_samples": blocked}

    # ---- 14. Focus scenes are the exact full-model crops (nozzle coupons shifted).
    focus_checks = {}
    clip = bd.Box(225.0, 320.0, 320.0).translate((-787.5, 0.0, 0.0))
    for label in BODY_FOCUS_LABELS:
        identical(focus[label], full[label] & clip)
        color_close(tuple(focus[label].color), tuple(full[label].color))
    focus_checks["body"] = {"clip_center_mm": [-787.5, 0.0, 0.0], "labels": 25}
    for name, labels, clip_center in (
        ("main_fin", MAIN_FIN_FOCUS_LABELS, (-1031.0, 108.0, 111.0)),
        ("booster_fin", BOOSTER_FIN_FOCUS_LABELS, (-1407.0, 108.0, 110.0)),
    ):
        clip = bd.Box(82.0, 76.0, 76.0).translate(clip_center)
        target = main_fin_focus if name == "main_fin" else booster_fin_focus
        for label in labels:
            identical(target[label], full[label] & clip)
            color_close(tuple(target[label].color), tuple(full[label].color))
        focus_checks[name] = {"clip_center_mm": list(clip_center), "labels": 7}
    main_clip = bd.Box(80.0, 220.0, 220.0).translate((-1090.0, 0.0, 0.0))
    booster_clip = bd.Box(90.0, 190.0, 190.0).translate((-1643.0, 0.0, 0.0))
    for label in NOZZLE_FOCUS_LABELS:
        if label.startswith("booster"):
            expected = (full[label] & booster_clip).moved(bd.Location((0.0, 130.0, 0.0)))
        else:
            expected = (full[label] & main_clip).moved(bd.Location((0.0, -130.0, 0.0)))
        identical(nozzle_focus[label], expected)
        color_close(tuple(nozzle_focus[label].color), tuple(full[label].color))
    focus_checks["nozzle_pair"] = {
        "main_shift_mm": [0.0, -130.0, 0.0], "booster_shift_mm": [0.0, 130.0, 0.0],
        "labels": 24,
    }

    # ---- 15. Outer envelope and inventory.
    total_length = full_scene.roots[0].shape().bounding_box().size.X
    assert abs(total_length - 3370.0) < 0.01, total_length
    assert family_counts["new_detail_total"] == 202
    assert family_counts["existing_r16_detail_total"] == 21
    assert family_counts["full_detail_total"] == 223
    assert family_counts["r16_primary_form_total"] == 23
    assert family_counts["full_part_total"] == 246
    assert family_counts["changed_host_total"] == 10
    assert family_counts["unchanged_r16_part_total"] == 34
    assert family_counts["full_part_total"] == len(full)

    report = {
        "ok": True,
        "status": "PASS",
        "baseline_r16_hash": baseline_scene.document_hash,
        "layout_manifest_baseline_hash": layout["baseline_document_hash"],
        "scenes": {
            name: {"document_hash": scenes[name]["scene"].document_hash,
                   "leaf_count": len(scenes[name]["rows"]),
                   "placements_valid": len(scenes[name]["rows"])}
            for name in SCENES
        },
        "saved_geometry_placements_validated": placements_validated,
        "inventory": {
            "full_part_total": len(full),
            "unchanged_r16_part_total": len(unchanged_labels),
            "changed_host_total": len(changed_hosts),
            "new_detail_total": len(new_labels),
            "existing_r16_detail_total": 21,
            "full_detail_total": 223,
            "r16_primary_form_total": 23,
        },
        "host_cuts": host_cuts,
        "new_detail_support": {
            "details_checked": len(support),
            "minimum_common_face_area_mm2": min(
                row["common_face_area_mm2"] for row in support.values()),
            "maximum_owner_overlap_mm3": max(
                row["overlap_mm3"] for row in support.values()),
            "all_within_old_host_skin": True,
        },
        "pair_interference": {
            "new_detail_pairs_bbox_candidates_boolean_checked": detail_pair_candidates,
            "new_detail_pair_overlaps_ge_0_01_mm3": len(detail_pair_overlaps),
            "new_vs_nonowner_baseline_bbox_candidates_boolean_checked": nonowner_candidates,
            "new_vs_nonowner_overlaps_ge_0_01_mm3": len(nonowner_overlaps),
            "legacy_baseline_pairs_preserved": True,
        },
        "fourfold_and_fold_copies_checked": len(fourfold),
        "seam_checks": {
            "groups_checked": len(seam_checks),
            "heads_visible_through_skin": 16,
            "details": seam_checks,
        },
        "slot_checks": {"fastener_heads_checked": len(slot_checks)},
        "nozzle_checks": nozzle_checks,
        "intake_channels": intake_checks,
        "focus_crops": focus_checks,
        "material_assignments_full": len(full_sidecar["appearance"]["assignments"]),
        "material_assignments_separated": len(separated_sidecar["appearance"]["assignments"]),
        "material_assignments_focus": focus_material_counts,
        "total_length_mm": total_length,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ("host_cuts", "seam_checks")}, indent=2))
    print("PASS: 555 saved placements valid; exact R16 preservation; localized",
          "host cuts; support contacts; pair clearances; fourfold/eightfold copies;",
          "seam visibility; nozzle bores; intake channels; materials; focus crops.")


def _rotate_point(point, clock_degrees):
    angle = math.radians(clock_degrees)
    x, y, z = point
    return (x, y * math.cos(angle) - z * math.sin(angle),
            y * math.sin(angle) + z * math.cos(angle))


if __name__ == "__main__":
    run_full()
