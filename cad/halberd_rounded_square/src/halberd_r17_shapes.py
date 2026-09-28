"""R17 full-detail composition over the cached R16 Halberd.

The fin and nozzle prototypes select faces from the saved R16 STEP.  Before
their cutters are used, the corresponding cached R16 leaves are checked
against those saved native hosts.  All new geometry remains editable here.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from cadgen import build123d as bd, read_scene, srgb

from halberd_r16 import halberd_r16
from halberd_r16_shapes import MATERIALS as R16_MATERIALS
from halberd_r17_interface_shapes import (
    FASTENER_BORE_RADIUS,
    FASTENER_COUNTERSINK_DEPTH,
    FASTENER_COUNTERSINK_TOP_RADIUS,
    FASTENER_HEAD_BOTTOM_RADIUS,
    FASTENER_HEAD_HEIGHT,
    FASTENER_HEAD_TOP_RADIUS,
    FASTENER_SEAT_DEPTH,
    FASTENER_SLOT_DEPTH,
    FASTENER_SLOT_LENGTH,
    FASTENER_SLOT_WIDTH,
    FASTENER_STEM_RADIUS,
    FASTENER_TOP_RECESS,
    INSET,
    METAL,
    build_r17_prototypes,
    load_r16_parts,
)


ROOT = Path(__file__).resolve().parents[1]
BASELINE_STEP = ROOT / "STEP" / "halberd_r16.step"
SEPARATION = 340.0
IDENTITY_VOLUME_TOLERANCE = 0.05

MAIN_BODY = "main_body_intake_r12"
BOOSTER_BODY = "booster_body"
MAIN_ACCESS_STATIONS = (
    (-950.0, 80.0, 18.0),
    (-750.0, 120.0, 26.0),
    (-550.0, 72.0, 18.0),
    (-80.0, 90.0, 22.0),
    (180.0, 120.0, 26.0),
    (440.0, 72.0, 18.0),
)
# x=-320 is the already-approved R16 family and is intentionally not rebuilt.
BOOSTER_ACCESS_STATIONS = ((-1450.0, 90.0, 22.0),)
ACCESS_CLOCKS = (0.0, 90.0, 180.0, 270.0)
SEAM_ROWS = (-850.0, -650.0, -200.0, 320.0)
FIN_CLOCKS = (0.0, 90.0, 180.0, 270.0)


def _rounded_profile(x_center, length, width, radius, z):
    return bd.RectangleRounded(length, width, radius).translate((x_center, 0.0, z))


def _x_cylinder(radius, z0, z1, x_center, y_center):
    return bd.Cylinder(radius, z1 - z0,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .translate((x_center, y_center, z0))


def _service_fastener_seat(x_center, y_center):
    bore = _x_cylinder(1.36, 98.5, 99.1, x_center, y_center)
    sink = bd.Cone(1.36, 2.12, 0.75,
                   align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .translate((x_center, y_center, 99.1))
    bore.label = f"seat_bore_{x_center:g}_{y_center:g}"
    sink.label = f"seat_countersink_{x_center:g}_{y_center:g}"
    return bore + sink


def _service_fastener(x_center, y_center):
    stem = _x_cylinder(1.3, 98.5, 99.1, x_center, y_center)
    head = bd.Cone(1.3, 1.78, 0.55,
                   align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .translate((x_center, y_center, 99.1))
    screw = stem + head
    slot = bd.Box(0.5, 2.5, 0.5).translate((x_center, y_center, 99.65))
    screw = screw - slot
    screw.color = srgb(METAL)
    return screw


def _rotate_cardinal(shape, clock_degrees):
    return shape.rotate(bd.Axis.X, -clock_degrees) if clock_degrees else shape


def _access_cover_parts(x_center, length, width, group_prefix, clock):
    """R13 cover proportions with the R17 locked floors and proportional screws."""
    lower = _rounded_profile(x_center, length, width, 3.0, 98.8)
    middle = _rounded_profile(x_center, length, width, 3.0, 99.5)
    upper = _rounded_profile(x_center, length - 0.7, width - 0.7, 2.65, 99.85)
    cover = bd.loft([lower, middle, upper], ruled=True)

    screw_offset = length / 2.0 - 12.0
    fastener_sites = (x_center - screw_offset, x_center + screw_offset)
    fastener_holes = []
    screws = []
    for index, site_x in enumerate(fastener_sites, 1):
        hole = _service_fastener_seat(site_x, 0.0)
        hole.label = f"{group_prefix}_screw_seat_{index}"
        fastener_holes.append(hole)
        screws.append(_service_fastener(site_x, 0.0))
    for hole in fastener_holes:
        cover = cover - hole

    border_outer = bd.extrude(
        _rounded_profile(x_center, length + 4.0, width + 4.0, 3.4, 98.8),
        amount=0.3,
    )
    border_inner = bd.extrude(
        _rounded_profile(x_center, length, width, 3.0, 98.5), amount=1.0)
    border = border_outer - border_inner

    cover.label = f"{group_prefix}_cover"
    cover.color = srgb("#B5BDC3")
    border.label = f"{group_prefix}_border"
    border.color = srgb("#505960")
    for index, screw in enumerate(screws, 1):
        screw.label = f"{group_prefix}_screw_{index}"
        screw.color = srgb(METAL)

    seat = bd.extrude(
        _rounded_profile(x_center, length + 4.0, width + 4.0, 3.4, 98.8),
        amount=2.0,
    )
    seat.label = f"{group_prefix}_seat"

    parts = [cover, border, *screws]
    cutters = [seat, *fastener_holes]
    placed_parts = []
    placed_cutters = []
    for item in parts:
        placed = _rotate_cardinal(item, clock)
        placed_parts.append(placed)
    for item in cutters:
        placed = _rotate_cardinal(item, clock)
        placed_cutters.append(placed)
    return placed_parts, placed_cutters, fastener_sites


def _seam_fastener_seat(x_center):
    # Unlike a cover seat, this bore must open through the original Z=100 skin.
    # The cover's short countersink stops at99.85 and would leave a hidden cap.
    site_x = x_center - 7.0
    bore = _x_cylinder(1.36, 98.5, 99.1, site_x, 0.0)
    sink = bd.Cone(1.36, 2.576, 1.2,
                   align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .translate((site_x, 0.0, 99.1))
    return bore + sink


def _seam_detail(x_center, group_prefix, clock):
    groove = bd.Box(1.3, 50.0, 0.6).translate((x_center, 0.0, 99.7))
    groove.label = f"{group_prefix}_groove"
    liner = bd.Box(1.1, 49.8, 0.4).translate((x_center, 0.0, 99.6))
    liner.label = f"{group_prefix}_liner"
    liner.color = srgb(METAL)
    screw = _service_fastener(x_center - 7.0, 0.0)
    screw.label = f"{group_prefix}_screw"
    screw.color = srgb(METAL)
    seat = _seam_fastener_seat(x_center)
    groove = _rotate_cardinal(groove, clock)
    liner = _rotate_cardinal(liner, clock)
    screw = _rotate_cardinal(screw, clock)
    seat = _rotate_cardinal(seat, clock)
    seat.label = f"{group_prefix}_screw_seat"
    return [liner, screw], [groove, seat]


def _same_geometry(actual, expected, tolerance=IDENTITY_VOLUME_TOLERANCE):
    if not actual or not expected:
        return False
    return (abs((actual - expected).volume) < tolerance and
            abs((expected - actual).volume) < tolerance)


def _stage_part(shape, label, stage):
    part = shape
    part.label = label
    if part.color is None:
        part.color = srgb(METAL)
    if not label.startswith(stage + "_"):
        raise ValueError(f"Stage ownership label does not begin with {stage}_: {label}")
    return part


def _fin_station(prototype, stage, occurrence, clock):
    host_label = prototype.host_label if occurrence == 1 else (
        f"main_fin_{occurrence}" if stage == "main" else
        f"booster_fin_fairing_{occurrence}")
    cutters = []
    for index, cutter in enumerate(prototype.cutters):
        placed_cutter = _rotate_cardinal(cutter.moved(bd.Location()), clock)
        placed_cutter.label = (
            f"{host_label}_r17_strip_pocket" if index == 0 else
            f"{host_label}_r17_fastener_seat_{index}"
        )
        cutters.append(placed_cutter)
    if stage == "main":
        part_labels = [f"main_r17_fin_{occurrence}_inset_strip"] + [
            f"main_r17_fin_{occurrence}_fastener_{i}" for i in range(1, 5)]
    else:
        part_labels = [f"booster_r17_fin_fairing_{occurrence}_inset_strip"] + [
            f"booster_r17_fin_fairing_{occurrence}_fastener_{i}"
            for i in range(1, 5)]
    parts = [
        _stage_part(_rotate_cardinal(part.moved(bd.Location()), clock), label,
                    "main" if stage == "main" else "booster")
        for part, label in zip(prototype.parts, part_labels)
    ]
    return host_label, cutters, parts


def _prototype_part_labels(prototype_key, stage):
    if "fin" in prototype_key:
        return None
    return ([f"{stage}_r17_nozzle_ring"] +
            [f"{stage}_r17_nozzle_fastener_{i}" for i in range(1, 9)])


def _append_family_parts(family_by_label, parts, family):
    for part in parts:
        if part.label in family_by_label:
            raise ValueError(f"Duplicate R17 family label: {part.label}")
        family_by_label[part.label] = family


def build_components():
    """Build and return baseline leaves, cutters, additions and validation map.

    ``baseline_parts`` are the leaves of the decorated/cached R16 child. The
    native face selectors are evaluated only on shapes read from saved R16.
    """
    if not BASELINE_STEP.is_file():
        raise FileNotFoundError(f"Saved R16 selector source is missing: {BASELINE_STEP}")
    # Ask the decorated child first, before importing/loading the native STEP
    # kernel input, so cadgen can resolve a current cached child cheaply.
    cached_model = halberd_r16()
    scene, saved_parts = load_r16_parts()
    baseline_parts = {part.label: part for part in cached_model.children}
    if len(baseline_parts) != len(cached_model.children):
        raise ValueError("Cached R16 child has duplicate leaf labels")
    if set(saved_parts) != set(baseline_parts):
        raise ValueError("Saved and cached R16 leaf-label sets differ")

    required_hosts = {MAIN_BODY, BOOSTER_BODY}
    required_hosts.update(f"main_fin_{i}" for i in range(1, 5))
    required_hosts.update(f"booster_fin_fairing_{i}" for i in range(1, 5))
    for label in required_hosts:
        if not _same_geometry(saved_parts[label], baseline_parts[label]):
            raise ValueError(
                f"Saved R16 host {label} does not match cached decorated R16; "
                "refusing to apply saved-face prototype cutters"
            )

    prototypes = build_r17_prototypes(saved_parts)
    cutters_by_host = {label: [] for label in sorted(required_hosts)}
    additions = []
    detail_owner = {}
    detail_family = {}
    contact_groups = []
    pose_transforms = []

    # Nozzle cutters are deliberately seeded before all panel/seam cuts on the
    # two body hosts; they share one saved native host boolean per stage.
    for key, stage, host_label in (
        ("main_nozzle", "main", MAIN_BODY),
        ("booster_nozzle", "booster", BOOSTER_BODY),
    ):
        prototype = prototypes[key]
        if prototype.host_label != host_label:
            raise ValueError(f"{key} prototype host mismatch: {prototype.host_label}")
        cutters_by_host[host_label].extend(prototype.cutters)
        labels = _prototype_part_labels(key, stage)
        parts = [
            _stage_part(part, label, stage)
            for part, label in zip(prototype.parts, labels)
        ]
        additions.extend(parts)
        _append_family_parts(detail_family, parts, "nozzle")
        detail_owner.update({part.label: host_label for part in parts})
        contact_groups.append({
            "key": f"{stage}_nozzle_lip",
            "host_label": host_label,
            "detail_labels": [part.label for part in parts],
            "intended_contact": "recessed annular seat and individual axial screw seats",
        })

    for stage, stations, host_label in (
        ("main", MAIN_ACCESS_STATIONS, MAIN_BODY),
        ("booster", BOOSTER_ACCESS_STATIONS, BOOSTER_BODY),
    ):
        for x_center, length, width in stations:
            row = f"xm{abs(int(x_center))}" if x_center < 0 else f"xp{int(x_center)}"
            for clock in ACCESS_CLOCKS:
                clock_name = f"{int(clock):03d}"
                group = f"{stage}_access_{row}_{clock_name}"
                parts, cutters, screw_sites = _access_cover_parts(
                    x_center, length, width, group, clock)
                cutters_by_host[host_label].extend(cutters)
                additions.extend(parts)
                family = {"cover": "service_cover", "border": "service_border",
                          "screw_1": "service_fastener", "screw_2": "service_fastener"}
                for part in parts:
                    key = ("cover" if part.label.endswith("_cover") else
                           "border" if part.label.endswith("_border") else
                           "screw_1" if part.label.endswith("_screw_1") else "screw_2")
                    detail_family[part.label] = family[key]
                    detail_owner[part.label] = host_label
                contact_groups.append({
                    "key": group,
                    "host_label": host_label,
                    "detail_labels": [part.label for part in parts],
                    "intended_contact": (
                        "cover and border seat floors at Z=98.8 mm; screw feet "
                        "contact matching host bores at Z=98.5 mm"
                    ),
                })
                pose_transforms.append({
                    "group": group,
                    "translation_mm": [x_center, 0.0, 0.0],
                    "rotation_axis": "X",
                    "rotation_degrees": -clock,
                    "screw_x_sites_mm": list(screw_sites),
                })

    for x_center in SEAM_ROWS:
        row = f"xm{abs(int(x_center))}" if x_center < 0 else f"xp{int(x_center)}"
        for clock in ACCESS_CLOCKS:
            group = f"main_seam_{row}_{int(clock):03d}"
            parts, cutters = _seam_detail(x_center, group, clock)
            cutters_by_host[MAIN_BODY].extend(cutters)
            additions.extend(parts)
            detail_family[parts[0].label] = "seam_liner"
            detail_family[parts[1].label] = "seam_fastener"
            detail_owner.update({part.label: MAIN_BODY for part in parts})
            contact_groups.append({
                "key": group,
                "host_label": MAIN_BODY,
                "detail_labels": [part.label for part in parts],
                "intended_contact": (
                    "liner floor at Z=99.4 mm; screw foot contacts matching blind "
                    "host seat at Z=98.5 mm"
                ),
            })
            pose_transforms.append({
                "group": group,
                "translation_mm": [x_center, 0.0, 0.0],
                "rotation_axis": "X",
                "rotation_degrees": -clock,
            })

    for key, stage, prototype_key in (
        ("main", "main", "main_fin"),
        ("booster", "booster", "booster_fin"),
    ):
        prototype = prototypes[prototype_key]
        for occurrence, clock in enumerate(FIN_CLOCKS, 1):
            host_label, cutters, parts = _fin_station(
                prototype, stage, occurrence, clock)
            if host_label not in cutters_by_host:
                raise ValueError(f"Unexpected fin host in R17 layout: {host_label}")
            expected_host = saved_parts[host_label]
            rotated_prototype_host = _rotate_cardinal(prototype.host_before, clock)
            if not _same_geometry(expected_host, rotated_prototype_host):
                raise ValueError(
                    f"Saved R16 fin host {host_label} is not the rigid X rotation "
                    "of its face-indexed station-1 prototype"
                )
            cutters_by_host[host_label].extend(cutters)
            additions.extend(parts)
            for part in parts:
                detail_family[part.label] = (
                    "fin_strip" if part.label.endswith("inset_strip") else
                    "fin_fastener")
                detail_owner[part.label] = host_label
            contact_groups.append({
                "key": f"{stage}_fin_{occurrence}_root_interface",
                "host_label": host_label,
                "detail_labels": [part.label for part in parts],
                "intended_contact": "pilot conformal inset and four recessed screw seats",
            })
            pose_transforms.append({
                "group": f"{stage}_fin_{occurrence}_root_interface",
                "rotation_axis": "X",
                "rotation_degrees": -clock,
                "source_occurrence": f"{stage}_fin_1" if stage == "main" else
                                     "booster_fin_fairing_1",
            })

    if len(additions) != 202 or len({part.label for part in additions}) != 202:
        raise ValueError("R17 additions must have 202 unique detail labels")
    if set(detail_owner) != {part.label for part in additions}:
        raise ValueError("R17 detail-owner map does not cover every new part")
    if set(detail_family) != {part.label for part in additions}:
        raise ValueError("R17 material-family map does not cover every new part")

    host_after = {}
    ordered_cutter_labels = {}
    for host_label, cutters in cutters_by_host.items():
        if not cutters:
            raise ValueError(f"No R17 cutters assigned to changed host {host_label}")
        original = saved_parts[host_label]
        tool_compound = bd.Compound(children=cutters,
                                    label=f"{host_label}_r17_cutters")
        changed = original - tool_compound
        changed.label = host_label
        changed.color = baseline_parts[host_label].color
        host_after[host_label] = changed
        ordered_cutter_labels[host_label] = [cutter.label for cutter in cutters]

    family_counts = {}
    for family in detail_family.values():
        family_counts[family] = family_counts.get(family, 0) + 1
    family_counts.update({
        "new_detail_total": len(additions),
        "existing_r16_detail_total": 21,
        "full_detail_total": len(additions) + 21,
        "r16_primary_form_total": 23,
        "full_part_total": len(baseline_parts) + len(additions),
        "changed_host_total": len(host_after),
        "unchanged_r16_part_total": len(baseline_parts) - len(host_after),
    })
    expected_families = {
        "service_cover": 28, "service_border": 28, "service_fastener": 56,
        "seam_liner": 16, "seam_fastener": 16, "fin_strip": 8,
        "fin_fastener": 32, "nozzle": 18,
    }
    for family, expected_count in expected_families.items():
        actual = family_counts.get(family, 0)
        if actual != expected_count:
            raise ValueError(f"R17 {family} count {actual}, expected {expected_count}")
    if family_counts["full_detail_total"] != 223 or family_counts["full_part_total"] != 246:
        raise ValueError(f"Unexpected R17 full composition counts: {family_counts}")

    return {
        "baseline_scene": scene,
        "baseline_parts": baseline_parts,
        "saved_baseline_parts": saved_parts,
        "prototypes": prototypes,
        "cutters_by_host": cutters_by_host,
        "ordered_cutter_labels_by_host": ordered_cutter_labels,
        "host_after_by_label": host_after,
        "new_parts": tuple(additions),
        "detail_owner": detail_owner,
        "detail_family": detail_family,
        "intended_contact_groups": tuple(contact_groups),
        "family_counts": family_counts,
        "pose_transforms": tuple(pose_transforms),
    }


def validate_native_components(components):
    """Small native shape preflight; the saved-artifact checker is a later gate."""
    baseline = components["baseline_parts"]
    saved = components["saved_baseline_parts"]
    changed = components["host_after_by_label"]
    if len(baseline) != 44 or len(changed) != 10:
        raise ValueError("R17 native preflight: unexpected R16/changed-host count")
    for label, after in changed.items():
        before = saved[label]
        if not before.is_valid or len(before.solids()) != 1 or before.solids()[0].volume <= 0:
            raise ValueError(f"R17 native preflight: invalid original host {label}")
        if not after.is_valid or len(after.solids()) != 1 or after.solids()[0].volume <= 0:
            raise ValueError(f"R17 native preflight: invalid cut host {label}")
        if (after - before).volume >= IDENTITY_VOLUME_TOLERANCE:
            raise ValueError(f"R17 native preflight: host gained volume {label}")
        if (before - after).volume <= 0.0:
            raise ValueError(f"R17 native preflight: host cuts removed no volume {label}")
    for part in components["new_parts"]:
        if not part.is_valid or len(part.solids()) != 1 or part.solids()[0].volume <= 0:
            raise ValueError(f"R17 native preflight: invalid new solid {part.label}")
        if not part.label.startswith(("main_", "booster_")):
            raise ValueError(f"R17 native preflight: missing stage prefix {part.label}")
    return {
        "status": "NATIVE_SHAPE_PREFLIGHT_PASS",
        "new_part_count": len(components["new_parts"]),
        "changed_host_count": len(changed),
        "unchanged_baseline_part_count": len(baseline) - len(changed),
        "full_part_count": len(baseline) + len(components["new_parts"]),
        "checked_native_facts": [
            "saved/cached prototype-host correspondence",
            "all ten changed hosts remain valid positive single solids",
            "all 202 added details remain valid positive single solids",
            "cut hosts lose volume and do not gain volume",
            "stage prefixes and exact layout/family counts",
        ],
    }


def build_r17():
    components = build_components()
    parts = []
    for label, original in components["baseline_parts"].items():
        parts.append(components["host_after_by_label"].get(label, original))
    parts.extend(components["new_parts"])
    labels = [part.label for part in parts]
    if len(parts) != 246 or len(set(labels)) != 246:
        raise ValueError("R17 assembled model must contain 246 uniquely labeled parts")
    return bd.Compound(children=parts, label="Halberd_R17_Full_Detail")


def build_r17_separated():
    full = build_r17()
    parts = [
        part.moved(bd.Location((-SEPARATION, 0.0, 0.0)))
        if part.label.startswith("booster_") else part
        for part in full.children
    ]
    return bd.Compound(children=parts, label="Halberd_R17_Full_Detail_Separated")


def _crop_part(part, clip):
    crop = part & clip
    if not crop or not crop.is_valid:
        raise ValueError(f"R17 focus crop is empty or invalid: {part.label}")
    crop.label = part.label
    crop.color = part.color
    return crop


def _focus_materials(labels):
    wanted = {f"#{label}" for label in labels}
    materials = deepcopy(MATERIALS)
    assignments = []
    for assignment in materials["assignments"]:
        targets = [target for target in assignment["targets"] if target in wanted]
        if targets:
            assignments.append({**assignment, "targets": targets})
    materials["assignments"] = assignments
    return materials


def build_r17_body_focus():
    full = build_r17()
    parts = {part.label: part for part in full.children}
    selected = [MAIN_BODY]
    selected.extend(
        f"main_access_{'xm750'}_{clock:03d}_{part_name}"
        for clock in (0, 90, 180, 270)
        for part_name in ("cover", "border", "screw_1", "screw_2")
    )
    selected.extend(
        f"main_seam_xm850_{clock:03d}_{part_name}"
        for clock in (0, 90, 180, 270)
        for part_name in ("liner", "screw")
    )
    if len(selected) != 25 or set(selected) - set(parts):
        raise ValueError("R17 body focus must select the full 25-part crop context")
    clip = bd.Box(225.0, 320.0, 320.0).translate((-787.5, 0.0, 0.0))
    return bd.Compound(children=[_crop_part(parts[label], clip) for label in selected],
                       label="Halberd_R17_Body_Detail_Focus")


def _fin_focus(stage):
    full = build_r17()
    parts = {part.label: part for part in full.children}
    if stage == "main":
        target_host = "main_fin_1"
        context = MAIN_BODY
        details = ["main_r17_fin_1_inset_strip"] + [
            f"main_r17_fin_1_fastener_{i}" for i in range(1, 5)]
        clip = bd.Box(82.0, 76.0, 76.0).translate((-1031.0, 108.0, 111.0))
    elif stage == "booster":
        target_host = "booster_fin_fairing_1"
        context = BOOSTER_BODY
        details = ["booster_r17_fin_fairing_1_inset_strip"] + [
            f"booster_r17_fin_fairing_1_fastener_{i}" for i in range(1, 5)]
        clip = bd.Box(82.0, 76.0, 76.0).translate((-1407.0, 108.0, 110.0))
    else:
        raise ValueError(f"Unknown R17 fin focus stage: {stage}")
    selected = [target_host, context, *details]
    if len(selected) != 7 or set(selected) - set(parts):
        raise ValueError(f"R17 {stage} fin focus requires final host/context and five details")
    return bd.Compound(children=[_crop_part(parts[label], clip) for label in selected],
                       label=f"Halberd_R17_{stage.title()}_Fin_Interface_Focus")


def build_r17_main_fin_focus():
    return _fin_focus("main")


def build_r17_booster_fin_focus():
    return _fin_focus("booster")


def _nozzle_coupon(full_parts, stage, host_label, clip, dark_labels, shift):
    selected = [host_label, *dark_labels]
    selected.extend([f"{stage}_r17_nozzle_ring"] + [
        f"{stage}_r17_nozzle_fastener_{i}" for i in range(1, 9)])
    if len(selected) != 12 or set(selected) - set(full_parts):
        raise ValueError(f"R17 {stage} nozzle focus selection is incomplete")
    children = []
    for label in selected:
        cropped = _crop_part(full_parts[label], clip)
        children.append(cropped.moved(bd.Location(shift)))
    return bd.Compound(children=children, label=f"r17_{stage}_nozzle_final_coupon")


def build_r17_nozzle_focus():
    full = build_r17()
    parts = {part.label: part for part in full.children}
    main_clip = bd.Box(80.0, 220.0, 220.0).translate((-1090.0, 0.0, 0.0))
    booster_clip = bd.Box(90.0, 190.0, 190.0).translate((-1643.0, 0.0, 0.0))
    main = _nozzle_coupon(
        parts, "main", MAIN_BODY,
        main_clip,
        ("main_nozzle_dark_recess", "main_nozzle_dark_floor"),
        (0.0, -130.0, 0.0),
    )
    booster = _nozzle_coupon(
        parts, "booster", BOOSTER_BODY,
        booster_clip,
        ("booster_nozzle_dark_recess", "booster_nozzle_dark_floor"),
        (0.0, 130.0, 0.0),
    )
    children = [*main.children, *booster.children]
    if len(children) != 24:
        raise ValueError("R17 final nozzle focus must contain 24 placements")
    return bd.Compound(children=children, label="Halberd_R17_Final_Nozzle_Pair_Focus")


def _all_new_labels():
    """Return a deterministic label inventory without constructing geometry."""
    labels = []
    for stage, stations in (("main", MAIN_ACCESS_STATIONS),
                            ("booster", BOOSTER_ACCESS_STATIONS)):
        for x_center, _, _ in stations:
            row = f"xm{abs(int(x_center))}" if x_center < 0 else f"xp{int(x_center)}"
            for clock in ACCESS_CLOCKS:
                prefix = f"{stage}_access_{row}_{int(clock):03d}"
                labels.extend([f"{prefix}_cover", f"{prefix}_border",
                               f"{prefix}_screw_1", f"{prefix}_screw_2"])
    for x_center in SEAM_ROWS:
        row = f"xm{abs(int(x_center))}" if x_center < 0 else f"xp{int(x_center)}"
        for clock in ACCESS_CLOCKS:
            prefix = f"main_seam_{row}_{int(clock):03d}"
            labels.extend([f"{prefix}_liner", f"{prefix}_screw"])
    for i in range(1, 5):
        labels.extend([f"main_r17_fin_{i}_inset_strip"] +
                      [f"main_r17_fin_{i}_fastener_{j}" for j in range(1, 5)])
        labels.extend([f"booster_r17_fin_fairing_{i}_inset_strip"] +
                      [f"booster_r17_fin_fairing_{i}_fastener_{j}"
                       for j in range(1, 5)])
    for stage in ("main", "booster"):
        labels.extend([f"{stage}_r17_nozzle_ring"] +
                      [f"{stage}_r17_nozzle_fastener_{i}" for i in range(1, 9)])
    return tuple(labels)


def write_layout_metadata(components, output_path=None):
    """Write the measured shape-free layout map for the next checker pass."""
    import json

    destination = Path(output_path) if output_path else ROOT / "reviews" / "halberd_r17_layout.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "R17_GATE2_BUILT_CHECKER_PENDING",
        "baseline_step": str(BASELINE_STEP),
        "baseline_document_hash": components["baseline_scene"].document_hash,
        "full_source": str(ROOT / "src" / "halberd_r17_shapes.py"),
        "baseline_labels": list(components["baseline_parts"]),
        "changed_hosts": {
            host: {
                "cutter_labels_ordered": components["ordered_cutter_labels_by_host"][host],
                "cutter_count": len(components["cutters_by_host"][host]),
                "final_host_label": components["host_after_by_label"][host].label,
            }
            for host in components["host_after_by_label"]
        },
        "new_parts": [
            {"label": part.label,
             "owner_host": components["detail_owner"][part.label],
             "family": components["detail_family"][part.label],
             "color_linear": list(part.color)}
            for part in components["new_parts"]
        ],
        "intended_contact_groups": list(components["intended_contact_groups"]),
        "family_counts": components["family_counts"],
        "pose_transforms": list(components["pose_transforms"]),
        "unchanged_baseline_labels": sorted(
            set(components["baseline_parts"]) - set(components["host_after_by_label"])),
        "focus_leaf_counts": {
            "body": 25, "main_fin": 7, "booster_fin": 7, "nozzle_pair": 24,
        },
    }
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return destination


MATERIALS = deepcopy(R16_MATERIALS)
MATERIALS["definitions"].update({
    "r17_service_paint": {"name": "R17 access cover paint", "roughness": 0.65,
                          "metalness": 0.15, "baseColor": "#B5BDC3"},
    "r17_service_border": {"name": "R17 recessed access border", "roughness": 0.9,
                           "metalness": 0.05, "baseColor": "#505960"},
    "r17_detail_metal": {"name": "R17 small metallic hardware", "roughness": 0.38,
                          "metalness": 0.65, "baseColor": METAL},
    "r17_inset": {"name": "R17 fin-root inset", "roughness": 0.65,
                   "metalness": 0.15, "baseColor": INSET},
})
R17_LABELS = _all_new_labels()
_FAMILY_LABELS = {
    family: [] for family in (
        "service_cover", "service_border", "service_fastener", "seam_liner",
        "seam_fastener", "fin_strip", "fin_fastener", "nozzle",
    )
}
for label in R17_LABELS:
    if "_access_" in label:
        family = ("service_cover" if label.endswith("_cover") else
                  "service_border" if label.endswith("_border") else
                  "service_fastener")
    elif "_seam_" in label:
        family = "seam_liner" if label.endswith("_liner") else "seam_fastener"
    elif "inset_strip" in label:
        family = "fin_strip"
    elif "_fin_" in label or "_fin_fairing_" in label:
        family = "fin_fastener"
    else:
        family = "nozzle"
    _FAMILY_LABELS[family].append(label)
for family, material in (
    ("service_cover", "r17_service_paint"),
    ("service_border", "r17_service_border"),
    ("service_fastener", "r17_detail_metal"),
    ("seam_liner", "r17_detail_metal"),
    ("seam_fastener", "r17_detail_metal"),
    ("fin_strip", "r17_inset"),
    ("fin_fastener", "r17_detail_metal"),
    ("nozzle", "r17_detail_metal"),
):
    MATERIALS["assignments"].append({
        "targets": [f"#{label}" for label in _FAMILY_LABELS[family]],
        "material": material,
    })

BODY_FOCUS_LABELS = (
    MAIN_BODY,
    *(f"main_access_xm750_{clock:03d}_{name}"
      for clock in (0, 90, 180, 270)
      for name in ("cover", "border", "screw_1", "screw_2")),
    *(f"main_seam_xm850_{clock:03d}_{name}"
      for clock in (0, 90, 180, 270) for name in ("liner", "screw")),
)
MAIN_FIN_FOCUS_LABELS = (
    "main_fin_1", MAIN_BODY, "main_r17_fin_1_inset_strip",
    *(f"main_r17_fin_1_fastener_{i}" for i in range(1, 5)),
)
BOOSTER_FIN_FOCUS_LABELS = (
    "booster_fin_fairing_1", BOOSTER_BODY,
    "booster_r17_fin_fairing_1_inset_strip",
    *(f"booster_r17_fin_fairing_1_fastener_{i}" for i in range(1, 5)),
)
NOZZLE_FOCUS_LABELS = (
    MAIN_BODY, "main_nozzle_dark_recess", "main_nozzle_dark_floor",
    "main_r17_nozzle_ring", *(f"main_r17_nozzle_fastener_{i}" for i in range(1, 9)),
    BOOSTER_BODY, "booster_nozzle_dark_recess", "booster_nozzle_dark_floor",
    "booster_r17_nozzle_ring",
    *(f"booster_r17_nozzle_fastener_{i}" for i in range(1, 9)),
)
BODY_FOCUS_MATERIALS = _focus_materials(BODY_FOCUS_LABELS)
MAIN_FIN_FOCUS_MATERIALS = _focus_materials(MAIN_FIN_FOCUS_LABELS)
BOOSTER_FIN_FOCUS_MATERIALS = _focus_materials(BOOSTER_FIN_FOCUS_LABELS)
NOZZLE_FOCUS_MATERIALS = _focus_materials(NOZZLE_FOCUS_LABELS)


if __name__ == "__main__":
    import json

    _components = build_components()
    _preflight = validate_native_components(_components)
    _manifest = write_layout_metadata(_components)
    print(json.dumps({**_preflight, "layout_manifest": str(_manifest),
                      "family_counts": _components["family_counts"]}, indent=2))
