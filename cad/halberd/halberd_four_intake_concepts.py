"""Four clean-sheet Halberd concepts constrained by one runtime envelope.

Millimeters; X forward, Z dorsal. The selected hybrid supplies dimensional
constraints only: no STEP geometry is imported or modified.
"""
from cadgen import build123d as bd, srgb

from halberd_concept_shapes import tagged, disk, barrel, clock, fin, visual_nozzle
from halberd_shoulder_variants import section


LENGTH = 3367.0
HALF = LENGTH / 2.0
SEAM = -336.7
WIDTH = 208.0
CORNER = 12.0
NOSE_BASE = 1080.0
INTAKE_LIMIT = 850.0
ANGLES = (45, 135, 225, 315)
MOUNT_STATIONS = (0.0, 480.0)

HULL = srgb("#A6ADAF")
TRIM = srgb("#626C70")
DARK = srgb("#252C30")
CERAMIC = srgb("#D3D5D1")

CONCEPTS = ("Razorback", "Manta", "Citadel", "Petal")


def reference_sustainer_envelope():
    return bd.loft([
        section(SEAM, 208, 208, 12),
        section(400, 208, 208, 12),
        section(650, 192, 192, 32),
        disk(850, 86),
        disk(NOSE_BASE, 86),
    ], ruled=True)


def reference_booster_envelope():
    return bd.loft([
        section(-HALF, 166.4, 166.4, 62.4),
        section(-HALF + 240, 208, 208, 78),
        section(-1000, 208, 208, 64),
        section(SEAM - 180, 208, 208, 12),
        section(SEAM, 208, 208, 12),
    ], ruled=True)


def clip_to_envelope(shape, envelope):
    """Remove only material outside the locked envelope.

    OCCT common can return an empty result when long source faces are coincident;
    cutting the measured excess and subtracting it is stable for these lofts.
    """
    excess = shape - envelope
    return shape - excess if excess.solids() else shape


def ellipse_profile(x, radial, half_width, half_height):
    return bd.Ellipse(half_height, half_width).rotate(bd.Axis.Y, 90).translate((x, 0, radial))


def rounded_profile(x, radial, width, height, radius):
    return bd.RectangleRounded(height, width, radius).rotate(bd.Axis.Y, 90).translate((x, 0, radial))


def diamond_profile(x, radial, half_width, half_height):
    wire = bd.Wire.make_polygon([
        (x, 0, radial + half_height),
        (x, half_width, radial),
        (x, 0, radial - half_height),
        (x, -half_width, radial),
    ], close=True)
    return bd.Face(wire)


def intake_recipe(key):
    """Return one +Z passage and its blind backing."""
    if key == "Razorback":
        profiles = [
            rounded_profile(340, 69, 24, 12, 2),
            rounded_profile(500, 79, 34, 17, 2),
            rounded_profile(665, 96, 58, 24, 3),
            rounded_profile(825, 105, 70, 28, 3),
        ]
        passage = bd.loft(profiles, ruled=True)
        backing = bd.loft([
            rounded_profile(338.5, 69, 23, 11, 2),
            rounded_profile(342.0, 69, 21, 9, 2),
        ], ruled=True)
    elif key == "Manta":
        profiles = [
            ellipse_profile(300, 67, 17, 8),
            ellipse_profile(470, 76, 29, 12),
            ellipse_profile(650, 94, 48, 18),
            ellipse_profile(835, 106, 43, 15),
        ]
        passage = bd.loft(profiles, ruled=False)
        backing = bd.loft([
            ellipse_profile(298.5, 67, 16, 7),
            ellipse_profile(302.0, 67, 14, 5.5),
        ], ruled=True)
    elif key == "Citadel":
        profiles = [
            rounded_profile(365, 72, 24, 12, 1.5),
            rounded_profile(515, 82, 36, 18, 1.5),
            rounded_profile(670, 96, 52, 24, 2),
            rounded_profile(820, 104, 56, 24, 2),
        ]
        passage = bd.loft(profiles, ruled=True)
        backing = bd.loft([
            rounded_profile(363.5, 72, 23, 11, 1.5),
            rounded_profile(367.0, 72, 19, 8, 1.5),
        ], ruled=True)
    else:
        profiles = [
            diamond_profile(320, 68, 14, 9),
            diamond_profile(480, 78, 24, 15),
            diamond_profile(645, 94, 34, 23),
            diamond_profile(830, 105, 31, 28),
        ]
        passage = bd.loft(profiles, ruled=False)
        backing = bd.loft([
            diamond_profile(318.5, 68, 13, 8),
            diamond_profile(322.0, 68, 10, 6),
        ], ruled=True)
    return passage, backing


def petal_structured_intake_recipe():
    """Rounded recessed-ramp passage and its blind aft backing."""
    passage = bd.loft([
        ellipse_profile(320, 62, 10, 5),
        ellipse_profile(500, 66, 16, 8),
        ellipse_profile(680, 74, 23, 10),
        ellipse_profile(810, 78, 25, 9),
        ellipse_profile(849, 78, 22, 7),
    ], ruled=True)
    backing = bd.loft([
        ellipse_profile(318.5, 62, 9, 4.5),
        ellipse_profile(322.0, 62, 7, 3.5),
    ], ruled=True)
    return passage, backing


def petal_ramp_chine(side):
    """One low guide rail along a recessed Petal ramp."""
    profiles = []
    for x, radial, offset, width, height, corner in (
        (610, 77.5, 24, 3.0, 2.0, 0.7),
        (700, 78.5, 29, 8.0, 4.0, 1.5),
        (810, 77.5, 28, 7.0, 3.0, 1.2),
        (848, 76.5, 23, 2.0, 1.5, 0.5),
    ):
        profiles.append(rounded_profile(x, radial, width, height, corner).translate((0, side * offset, 0)))
    return bd.loft(profiles, ruled=True)


def petal_sustainer_raw():
    # The stage interface remains matched, but the former square waist is gone.
    return bd.loft([
        section(SEAM, 196, 196, 94),
        section(-120, 196, 196, 94),
        section(260, 184, 184, 88),
        section(560, 160, 160, 76),
        section(850, 156, 156, 74),
        section(NOSE_BASE, 166, 166, 80),
    ], ruled=True)


def sustainer_body(key):
    if key == "Razorback":
        raw = bd.loft([
            section(SEAM, 208, 208, 12),
            section(140, 204, 188, 6),
            section(430, 198, 184, 8),
            section(650, 184, 176, 16),
            section(820, 174, 174, 34),
            section(NOSE_BASE, 164, 164, 80),
        ], ruled=True)
    elif key == "Manta":
        raw = bd.loft([
            section(SEAM, 208, 208, 12),
            section(20, 206, 192, 88),
            section(390, 204, 164, 78),
            section(660, 184, 158, 74),
            section(880, 168, 168, 82),
            section(NOSE_BASE, 166, 166, 81),
        ], ruled=True)
    elif key == "Citadel":
        raw = bd.loft([
            section(SEAM, 208, 208, 12),
            section(80, 208, 202, 5),
            section(390, 202, 196, 5),
            section(640, 188, 184, 8),
            section(815, 174, 174, 18),
            section(NOSE_BASE, 164, 164, 30),
        ], ruled=True)
    else:
        raw = petal_sustainer_raw()
    # Preserve the fixed rack-contact stations even on shallow body concepts.
    for x in MOUNT_STATIONS:
        raw = raw.fuse(bd.Box(70, 30, 34).translate((x, 0, 85)))
    body = clip_to_envelope(raw, reference_sustainer_envelope())
    if key == "Petal":
        for angle in ANGLES:
            for side in (-1, 1):
                chine = clock(petal_ramp_chine(side), angle)
                chine = clip_to_envelope(chine, reference_sustainer_envelope())
                body = body.fuse(chine)
        passage, _ = petal_structured_intake_recipe()
    else:
        passage, _ = intake_recipe(key)
    for angle in ANGLES:
        body -= clock(passage, angle)
    body -= barrel(SEAM - 1, SEAM + 70, WIDTH * 0.31)
    return body


def petal_intake_prototype_body():
    """One structured intake at 45 degrees; three baseline cuts aid comparison."""
    raw = petal_sustainer_raw()
    for x in MOUNT_STATIONS:
        raw = raw.fuse(bd.Box(70, 30, 34).translate((x, 0, 85)))
    body = clip_to_envelope(raw, reference_sustainer_envelope())
    baseline_passage, _ = intake_recipe("Petal")
    for angle in ANGLES[1:]:
        body -= clock(baseline_passage, angle)
    structured_passage, _ = petal_structured_intake_recipe()
    body -= clock(structured_passage, ANGLES[0])
    body -= barrel(SEAM - 1, SEAM + 70, WIDTH * 0.31)
    return body


def radome(key):
    if key == "Razorback":
        return bd.loft([
            section(NOSE_BASE, 164, 164, 28),
            section(1280, 142, 132, 18),
            section(1480, 88, 72, 8),
            section(1620, 25, 21, 3),
            section(HALF, 1.2, 1.2, 0.2),
        ], ruled=True)
    if key == "Manta":
        return bd.loft([
            section(NOSE_BASE, 166, 166, 81), section(1290, 156, 148, 70),
            section(1480, 104, 88, 40), section(1615, 34, 25, 10),
            section(HALF, 1.2, 1.0, 0.2),
        ], ruled=False)
    if key == "Citadel":
        return bd.loft([
            section(NOSE_BASE, 164, 164, 16),
            section(1250, 150, 144, 12),
            section(1430, 108, 96, 7),
            section(1570, 58, 44, 3),
            section(HALF, 1.2, 1.2, 0.2),
        ], ruled=True)
    return bd.loft([
        section(NOSE_BASE, 166, 166, 80), section(1260, 164, 164, 79),
        section(1450, 118, 118, 55), section(1595, 48, 48, 21),
        section(HALF, 1.2, 1.2, 0.2),
    ], ruled=False)


def booster_body(key):
    if key == "Razorback":
        raw = bd.loft([
            section(-HALF, 158, 158, 7),
            section(-1450, 190, 184, 9),
            section(-1030, 202, 192, 9),
            section(-560, 208, 202, 10),
            section(SEAM, 208, 208, 12),
        ], ruled=True)
    elif key == "Manta":
        raw = bd.loft([
            section(-HALF, 164, 154, 72),
            section(-1420, 202, 182, 86),
            section(-930, 206, 190, 90),
            section(SEAM, 208, 208, 12),
        ], ruled=False)
    elif key == "Citadel":
        raw = bd.loft([
            section(-HALF, 160, 160, 8),
            section(-1470, 176, 176, 8),
            section(-1250, 198, 198, 8),
            section(-870, 198, 198, 8),
            section(-650, 208, 208, 10),
            section(SEAM, 208, 208, 12),
        ], ruled=True)
    else:
        raw = bd.loft([
            section(-HALF, 152, 152, 72), section(-1450, 184, 184, 88),
            section(-1120, 194, 194, 93), section(-760, 190, 190, 91),
            section(SEAM, 196, 196, 94),
        ], ruled=False)
    booster = clip_to_envelope(raw, reference_booster_envelope())
    booster -= barrel(-HALF - 1, -HALF + 75, WIDTH * 0.31 * 0.82)
    booster -= bd.loft([disk(SEAM - 10, WIDTH * 0.31 * 0.68),
                        disk(SEAM + 1, WIDTH * 0.31 * 0.8)], ruled=True)
    return booster


def fin_specs(key, booster=False):
    if not booster:
        return {
            "Razorback": (SEAM + 70, SEAM + 510, SEAM + 20, SEAM + 235, 220, 108, 9),
            "Manta": (SEAM + 100, SEAM + 570, SEAM + 210, SEAM + 420, 190, 101, 7),
            "Citadel": (SEAM + 55, SEAM + 355, SEAM + 25, SEAM + 185, 214, 108, 13),
            "Petal": (SEAM + 115, SEAM + 480, SEAM + 195, SEAM + 365, 202, 94, 8),
        }[key]
    return {
        "Razorback": (-HALF + 90, -HALF + 610, -HALF + 30, -HALF + 280, 242, 94, 11),
        "Manta": (-HALF + 130, -HALF + 760, -HALF + 260, -HALF + 540, 218, 96, 9),
        "Citadel": (-HALF + 75, -HALF + 470, -HALF + 35, -HALF + 220, 238, 96, 15),
        "Petal": (-HALF + 120, -HALF + 650, -HALF + 235, -HALF + 470, 226, 94, 10),
    }[key]


def build_concept(key):
    if key not in CONCEPTS:
        raise ValueError(f"Unknown four-intake concept: {key}")
    parts = [tagged(sustainer_body(key), "sustainer_body")]
    parts.append(tagged(radome(key), "radome", CERAMIC))
    parts.append(tagged(visual_nozzle(SEAM, 70, WIDTH * 0.31), "sustainer_nozzle", TRIM))
    _, backing = petal_structured_intake_recipe() if key == "Petal" else intake_recipe(key)
    for index, angle in enumerate(ANGLES, 1):
        parts.append(tagged(clock(backing, angle), f"intake_floor_{index}", DARK))
        parts.append(tagged(clock(fin(*fin_specs(key)), angle), f"sustainer_fin_{index}", TRIM))
    parts.append(tagged(booster_body(key), "booster_body"))
    parts.append(tagged(visual_nozzle(-HALF, 75, WIDTH * 0.31 * 0.82), "booster_nozzle", TRIM))
    for index, angle in enumerate(ANGLES, 1):
        parts.append(tagged(clock(fin(*fin_specs(key, booster=True)), angle), f"booster_fin_{index}", TRIM))
    for index, x in enumerate(MOUNT_STATIONS, 1):
        parts.append(tagged(bd.Box(62, 25, 10).translate((x, 0, 105)), f"mount_{index}", TRIM))
    return bd.Compound(children=parts, label=f"Halberd_{key}")


def build_separated_review(key):
    model = build_concept(key)
    children = []
    for child in model.children:
        if child.label.startswith("booster_"):
            child = child.translate((-350, 0, 0))
        children.append(child)
    return bd.Compound(children=children, label=f"Halberd_{key}_Separated")


def build_intake_review(key):
    model = build_concept(key)
    crop = bd.Box(620, 520, 520).translate((560, 0, 0))
    children = []
    for child in model.children:
        if child.label == "sustainer_body":
            clipped = child & crop
            clipped.label = child.label
            clipped.color = child.color
            children.append(clipped)
        elif child.label.startswith("intake_floor_"):
            children.append(child)
    return bd.Compound(children=children, label=f"Halberd_{key}_Intakes")


def build_petal_intake_prototype():
    """Full Petal context with one recessed ramp and three baseline slits."""
    model = build_concept("Petal")
    _, structured_backing = petal_structured_intake_recipe()
    _, baseline_backing = intake_recipe("Petal")
    children = []
    for child in model.children:
        if child.label == "sustainer_body":
            children.append(tagged(petal_intake_prototype_body(), "sustainer_body"))
        elif child.label == "intake_floor_1":
            children.append(tagged(clock(structured_backing, ANGLES[0]), child.label, DARK))
        elif child.label.startswith("intake_floor_"):
            index = int(child.label.rsplit("_", 1)[1]) - 1
            children.append(tagged(clock(baseline_backing, ANGLES[index]), child.label, DARK))
        else:
            children.append(child)
    for side, label in ((-1, "port"), (1, "starboard")):
        chine = clock(petal_ramp_chine(side), ANGLES[0])
        chine = clip_to_envelope(chine, reference_sustainer_envelope())
        children.append(tagged(chine, f"intake_chine_{label}_prototype", HULL))
    return bd.Compound(children=children, label="Halberd_Petal_Intake_Prototype")


def build_petal_intake_prototype_closeup():
    model = build_petal_intake_prototype()
    crop = bd.Box(620, 520, 520).translate((570, 0, 0))
    children = []
    for child in model.children:
        if child.label not in ("sustainer_body", "intake_floor_1") and not child.label.startswith("intake_chine_"):
            continue
        clipped = child & crop
        if clipped is not None and clipped.volume > 1e-6:
            clipped.label = child.label
            clipped.color = child.color
            children.append(clipped)
    return bd.Compound(children=children, label="Halberd_Petal_Intake_Prototype_Closeup")
