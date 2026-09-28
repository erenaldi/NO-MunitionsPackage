"""Approximate PL-10 exterior art model reconstructed from five perspective renders.

Millimeters; aft face at Z=0, nose along +Z. Dimensions describe an artistic
display model, not real hardware. No internal mechanisms or functional interfaces.
The original Kris and its exports are deliberately not imported or modified.
"""

from cadgen import build123d as bd
from cadgen import report, srgb, step


LENGTH = 2870.0
BODY_RADIUS = 80.0
REFERENCE_LENGTH = 2870.0
REFERENCE_RADIUS = 80.0
AZIMUTHS = (0.0, 90.0, 180.0, 270.0)
TAIL_TIP_RADIUS = 190.0
STRAKE_TIP_RADIUS = 124.0
FIN_THICKNESS = 6.0
SEAM_WIDTH = 1.8
BODY_SEAMS = (420.0, 1350.0, 1700.0, 2070.0, 2430.0, 2640.0)
BODY_COLOR = srgb("#C8CDCB")
HARDWARE_COLOR = srgb("#959E9D")
DARK_COLOR = srgb("#343B3D")
WINDOW_COLOR = srgb("#18252A")


def cylinder(z0, z1, radius):
    return bd.Cylinder(
        radius, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    ).translate((0, 0, z0))


def skin_patch(z0, z1, width, outer_radius=81.4, inner_radius=79.8):
    shell = cylinder(z0, z1, outer_radius) - cylinder(z0 - 1, z1 + 1, inner_radius)
    mask = bd.Box(30, width, z1 - z0).translate((80, 0, (z0 + z1) / 2))
    return shell & mask


def beveled_plate(points, thickness=FIN_THICKNESS, bevel=1.0):
    # Four perimeter sections give the cosmetic plate a narrow beveled rim.
    cx = sum(x for x, z in points) / len(points)
    cz = sum(z for x, z in points) / len(points)
    inset = [(cx + (x - cx) * 0.965, cz + (z - cz) * 0.965) for x, z in points]
    sections = []
    for y, profile in (
        (-thickness / 2, inset),
        (-thickness / 2 + bevel, points),
        (thickness / 2 - bevel, points),
        (thickness / 2, inset),
    ):
        sections.append(bd.Wire.make_polygon([(x, y, z) for x, z in profile], close=True))
    return bd.Solid.make_loft(sections, ruled=True)


def raised_strip(z0, z1, width, height):
    sections = []
    for z, h, w in (
        (z0, 0.6, width * 0.4),
        (z0 + 28, height, width),
        (z1 - 28, height, width),
        (z1, 0.6, width * 0.4),
    ):
        sections.append(bd.Wire.make_polygon([
            (78.0, -w / 2, z), (80 + h, -w * 0.30, z),
            (80 + h, w * 0.30, z), (78.0, w / 2, z),
        ], close=True))
    return bd.Solid.make_loft(sections, ruled=True)


def fastener(z, radius=80.6, head_radius=2.2):
    head = cylinder(0, 1.0, head_radius).rotate(bd.Axis.Y, 90).translate((radius, 0, z))
    slot = bd.Box(2, 0.6, head_radius * 1.3).translate((radius + 1, 0, z))
    return head - slot


@step(out="PL-10_Exterior.step")
def pl10():
    parts = []

    def add(shape, label, color=BODY_COLOR, angle=0.0):
        shape = shape.rotate(bd.Axis.Z, angle)
        # Scale the entire labeled exterior consistently; no fixed-position details.
        shape = shape.scale((BODY_RADIUS / REFERENCE_RADIUS,
                             BODY_RADIUS / REFERENCE_RADIUS,
                             LENGTH / REFERENCE_LENGTH))
        shape.label = label
        shape.color = color
        shape.cad_material = {"roughness": 0.6, "metalness": 0.15}
        parts.append(shape)

    report("body sections and nose")
    starts = (110.0,) + tuple(z + SEAM_WIDTH for z in BODY_SEAMS)
    ends = BODY_SEAMS + (2780.0,)
    for i, (z0, z1) in enumerate(zip(starts, ends)):
        add(cylinder(z0, z1, REFERENCE_RADIUS), f"body_section_{i + 1:02d}")
    for i, z in enumerate(BODY_SEAMS):
        add(cylinder(z, z + SEAM_WIDTH, 79.65), f"recessed_section_seam_{i + 1:02d}", DARK_COLOR)
    add(cylinder(30, 110, 80), "aft_collar")
    add(cylinder(104, 109, 81), "aft_collar_rim", HARDWARE_COLOR)

    fairing = bd.loft([
        bd.Circle(radius).translate((0, 0, z))
        for z, radius in ((2780, 80), (2810, 79.5), (2834, 77))
    ], ruled=False)
    add(fairing, "nose_window_fairing")
    add(cylinder(2834, 2838, 77), "nose_window_bezel", HARDWARE_COLOR)
    cap_height, cap_radius = 32.0, 77.0
    sphere_radius = (cap_radius ** 2 + cap_height ** 2) / (2 * cap_height)
    dome = bd.Sphere(sphere_radius).translate((0, 0, REFERENCE_LENGTH - sphere_radius))
    dome = dome & cylinder(2838, REFERENCE_LENGTH + 1, 78)
    add(dome, "dark_nose_window", WINDOW_COLOR)
    parts[-1].cad_material = {"roughness": 0.2, "metalness": 0.1, "clearcoat": 1.0}

    report("strakes and tail fins")
    strake = beveled_plate([
        (78, 620), (STRAKE_TIP_RADIUS, 660),
        (STRAKE_TIP_RADIUS, 1590), (96, 1730), (78, 1790),
    ])
    tail = beveled_plate([
        (78, 125), (TAIL_TIP_RADIUS, 76), (TAIL_TIP_RADIUS, 214), (78, 353),
    ], thickness=7.0)
    for index, angle in enumerate(AZIMUTHS, 1):
        add(strake, f"long_body_strake_{index}", angle=angle)
        add(raised_strip(614, 1800, 15, 3), f"strake_root_fairing_{index}", angle=angle)
        add(tail, f"tail_fin_{index}", angle=angle)
        add(raised_strip(118, 355, 19, 5), f"tail_fin_root_cover_{index}", HARDWARE_COLOR, angle)
        boss = cylinder(0, 7, 11).rotate(bd.Axis.Y, 90).translate((80, 0, 224))
        add(boss, f"tail_root_round_cover_{index}", HARDWARE_COLOR, angle)

    report("exterior panels, strips and cosmetic fittings")
    # Shallow curved overlays represent visible panel breaks, not working hatches.
    for index, angle in enumerate((45.0, 225.0), 1):
        add(skin_patch(461, 576, 42), f"aft_access_panel_{index}", HARDWARE_COLOR, angle)
        for z in (473, 564):
            add(fastener(z, 81.2), f"aft_panel_fastener_{index}_{int(z)}", DARK_COLOR, angle)
        add(raised_strip(2010, 2390, 12, 4), f"forward_raised_strip_{index}", angle=angle)
        add(skin_patch(2500, 2640, 26, 81.0), f"nose_access_panel_{index}", angle=angle)

    for index, angle in enumerate((110.0, 290.0), 1):
        for slot_index, z in enumerate((2180.0, 2240.0), 1):
            add(skin_patch(z, z + 35, 13, 80.5, 79.9),
                f"dark_surface_inset_{index}_{slot_index}", DARK_COLOR, angle)
    for index, angle in enumerate((45.0, 135.0, 225.0, 315.0), 1):
        for z in (401.0, 1366.0, 2447.0, 2760.0):
            add(fastener(z, 79.8), f"surface_fastener_{index}_{int(z)}", HARDWARE_COLOR, angle)

    # Topside fittings are visual approximations only, with no mating specification.
    for index, z in enumerate((965.0, 1640.0), 1):
        add(skin_patch(z - 44, z + 44, 28, 83), f"top_fitting_base_{index}", HARDWARE_COLOR, 45)
        fitting = bd.Box(15, 14, 58).translate((87, 0, z))
        add(fitting, f"top_fitting_block_{index}", HARDWARE_COLOR, 45)

    report("aft exterior recess")
    # A blind cosmetic recess supplies the visible dark aft opening, not a nozzle design.
    cup = cylinder(0, 30, 60) - cylinder(-1, 21, 45)
    add(cup, "aft_cosmetic_recess_rim", HARDWARE_COLOR)
    add(cylinder(20.8, 21.1, 44.8), "aft_recess_dark_back", DARK_COLOR)
    for index, angle in enumerate(AZIMUTHS, 1):
        tab = bd.Box(24, 12, 32).translate((62, 0, 24))
        add(tab, f"aft_external_tab_{index}", HARDWARE_COLOR, angle)

    model = bd.Compound(children=parts, label="PL10_Approximate_Exterior")
    bounds = model.bounding_box()
    if abs(bounds.size.Z - LENGTH) > 0.01:
        raise ValueError(f"Unexpected display length: {bounds.size.Z}")
    if len({part.label for part in parts}) != len(parts):
        raise ValueError("Duplicate exterior part labels")
    return model


if __name__ == "__main__":
    pl10()
