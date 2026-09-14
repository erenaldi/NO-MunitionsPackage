"""Parametric AAM-44 Halberd exterior at final game scale, in millimeters.

The missile axis is X, nose forward. The runtime pivot is at X=0. Viewed from
the nose, the three intake-fin planes are at 2, 6, and 10 o'clock, leaving the
12-o'clock sector clear for the launch rail and suspension hardware.
"""

import math

from cadgen import build123d as bd
from cadgen import report, srgb, step


LENGTH = 3367.0
HALF_LENGTH = LENGTH * 0.5
BODY_RADIUS = 100.5
SEAM_X = -336.7

# RC1 exterior-only cavity and surface-detail datums; no motor simulation inputs.
SUSTAINER_RECESS_DEPTH = 82.0
SUSTAINER_RECESS_RADIUS = 76.0
PANEL_GROOVE_WIDTH = 1.4
PANEL_GROOVE_DEPTH = 0.65

NOSE_BASE_X = 1190.0
FORWARD_BAND_X = 1040.0
RAMJET_BAND_X = 300.0
INTAKE_FRONT_X = 790.0
INTAKE_THROAT_X = 690.0
INTAKE_AFT_X = 30.0
INTAKE_DUCT_AFT_X = 45.0
STRAKE_AFT_X = 130.0

INTAKE_HEIGHT_SCALE = 0.85
INTAKE_MOUTH_WIDTH = 72.0
INTAKE_MOUTH_HEIGHT = 47.0 * INTAKE_HEIGHT_SCALE
INTAKE_THROAT_WIDTH = 42.0
INTAKE_THROAT_HEIGHT = 25.0 * INTAKE_HEIGHT_SCALE
INTAKE_LIP_MIN_THICKNESS = 5.0
INTAKE_DUCT_DEPTH = INTAKE_FRONT_X - INTAKE_DUCT_AFT_X

MOUNT_RAIL_LENGTH = 920.0
MOUNT_RAIL_WIDTH = 10.0
MOUNT_RAIL_HEIGHT = 3.5
MOUNT_LUG_LENGTH = 44.0
MOUNT_LUG_WIDTH = 18.0
MOUNT_LUG_HEIGHT = 8.0
MOUNT_CONDUIT_LENGTH = 520.0
MOUNT_CONDUIT_WIDTH = 5.0
MOUNT_CONDUIT_HEIGHT = 2.0
MOUNT_LUG_STATIONS = (-75.0, 410.0)

SUSTAINER_FIN_ROOT_AFT_X = SEAM_X + 36.7
SUSTAINER_FIN_ROOT_FORWARD_X = STRAKE_AFT_X
SUSTAINER_FIN_TIP_AFT_X = -215.0
SUSTAINER_FIN_TIP_FORWARD_X = 45.0
SUSTAINER_FIN_RADIUS = 172.0

BOOSTER_NOZZLE_START_X = -1510.0
BOOSTER_NOZZLE_THROAT_X = -1585.0
BOOSTER_NOZZLE_EXIT_RADIUS = 80.0
BOOSTER_NOZZLE_THROAT_RADIUS = 27.0
BOOSTER_NOZZLE_CHAMBER_RADIUS = 72.0
BOOSTER_NOZZLE_LINER_THICKNESS = 5.0
BOOSTER_FIN_AFT_X = -1515.0
BOOSTER_FIN_FORWARD_X = -610.0
BOOSTER_FIN_TIP_AFT_X = -1395.0
BOOSTER_FIN_TIP_FORWARD_X = -1145.0
BOOSTER_FIN_SHOULDER_X = -1025.0
BOOSTER_FIN_SHOULDER_RADIUS = 125.0
BOOSTER_FIN_RADIUS = 218.0

INTAKE_AZIMUTHS = (60.0, 180.0, 300.0)

BODY_COLOR = srgb("#AEB4B5")
RADOME_COLOR = srgb("#C5C9C7")
FIN_COLOR = srgb("#62696B")
HARDWARE_COLOR = srgb("#4D5558")
INTAKE_COLOR = srgb("#252B2D")
BOOSTER_COLOR = srgb("#9CA3A3")
SUSTAINER_NOZZLE_COLOR = srgb("#34393C")
NOZZLE_COLOR = srgb("#4A211B")


def circle_x(x, radius):
    return bd.Circle(radius).rotate(bd.Axis.Y, 90.0).translate((x, 0.0, 0.0), transform=True)


def cylinder_x(x_min, x_max, radius):
    return (
        bd.Cylinder(radius, x_max - x_min, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        .rotate(bd.Axis.Y, 90.0)
        .translate((x_min, 0.0, 0.0), transform=True)
    )


def annular_cylinder_x(x_min, x_max, outer_radius, inner_radius):
    return cylinder_x(x_min, x_max, outer_radius) - cylinder_x(
        x_min - 0.5, x_max + 0.5, inner_radius
    )


def tapered_band(x_min, x_max, radius, rise, bevel=5.0):
    """Seated annular trim, with sloped shoulders instead of stacked solid drums."""
    outer = bd.loft([
        circle_x(x_min, radius), circle_x(x_min + bevel, radius + rise),
        circle_x(x_max - bevel, radius + rise), circle_x(x_max, radius),
    ], ruled=True)
    return outer - cylinder_x(x_min - 1.0, x_max + 1.0, radius - 2.0)


def panel_ring(part, x, radius=BODY_RADIUS):
    return part - annular_cylinder_x(
        x - PANEL_GROOVE_WIDTH / 2, x + PANEL_GROOVE_WIDTH / 2,
        radius + 1.0, radius - PANEL_GROOVE_DEPTH,
    )


def make_sustainer_nozzle():
    """Blind visual recess: a dark closed backing, not internal engine geometry."""
    shoulder = tapered_band(SEAM_X, SEAM_X + 28.0, BODY_RADIUS, 3.0, 4.0)
    sleeve = cylinder_x(SEAM_X, SEAM_X + SUSTAINER_RECESS_DEPTH, SUSTAINER_RECESS_RADIUS)
    cavity = bd.loft([
        circle_x(SEAM_X - 1.0, 70.0),
        circle_x(SEAM_X + 9.0, 70.0),
        circle_x(SEAM_X + 60.0, 39.0),
        circle_x(SEAM_X + SUSTAINER_RECESS_DEPTH - 4.0, 32.0),
    ], ruled=True)
    # Radial bridge joins the trim to the recessed sleeve without closing its mouth.
    bridge = annular_cylinder_x(SEAM_X + 1.0, SEAM_X + 5.0, BODY_RADIUS, 70.0)
    return shoulder.fuse(sleeve, bridge) - cavity


def make_ramjet_body():
    body = cylinder_x(SEAM_X, RAMJET_BAND_X, BODY_RADIUS)
    body -= cylinder_x(SEAM_X - 1.0, SEAM_X + SUSTAINER_RECESS_DEPTH,
                       SUSTAINER_RECESS_RADIUS)
    return body


def root_fairing(sections):
    """Tapered hexagonal saddle, embedded into the body with narrow shoulders."""
    wires = []
    for x, width, height in sections:
        bottom = BODY_RADIUS - 4.0
        top = BODY_RADIUS + height
        wires.append(bd.Wire.make_polygon([
            (x, -width / 2, bottom), (x, width / 2, bottom),
            (x, width / 2, BODY_RADIUS), (x, width * 0.23, top),
            (x, -width * 0.23, top), (x, -width / 2, BODY_RADIUS),
        ], close=True))
    return bd.Solid.make_loft(wires, ruled=True)


def profile_prism(points, width):
    wire = bd.Wire.make_polygon(
        [(x, -width * 0.5, radial) for x, radial in points], close=True
    )
    return bd.Solid.extrude(bd.Face(wire), (0.0, width, 0.0))


def symmetric_aerofoil_wire(z, trailing_x, leading_x, thickness, samples=18):
    chord = leading_x - trailing_x
    if chord <= 0.0:
        raise ValueError("Aerofoil leading edge must be forward of its trailing edge")

    stations = [index / samples for index in range(samples + 1)]
    ordinates = [
        0.2969 * math.sqrt(station)
        - 0.1260 * station
        - 0.3516 * station**2
        + 0.2843 * station**3
        - 0.1036 * station**4
        for station in stations
    ]
    scale = thickness * 0.5 / max(ordinates)
    upper = [
        (leading_x - station * chord, ordinate * scale, z)
        for station, ordinate in zip(stations, ordinates)
    ]
    lower = [(x, -y, section_z) for x, y, section_z in reversed(upper[1:-1])]
    return bd.Wire.make_polygon([*upper, *lower], close=True)


def aerofoil_loft(sections, ruled=True):
    return bd.Solid.make_loft(
        [symmetric_aerofoil_wire(*section) for section in sections],
        ruled=ruled,
    )


def trapezoid_wire_x(x, bottom_z, bottom_half_width, top_z, top_half_width, top_x=None):
    top_x = x if top_x is None else top_x
    return bd.Wire.make_polygon(
        [
            (x, -bottom_half_width, bottom_z),
            (x, bottom_half_width, bottom_z),
            (top_x, top_half_width, top_z),
            (top_x, -top_half_width, top_z),
        ],
        close=True,
    )


def loft_trapezoids(sections):
    return bd.loft(
        [bd.Face(trapezoid_wire_x(*section)) for section in sections],
        ruled=True,
    )


def intake_cheek_section(section, side, thickness=5.0, overlap=1.5):
    x, bottom_z, bottom_half_width, top_z, top_half_width = section
    return bd.Face(
        bd.Wire.make_polygon(
            [
                (x, side * (bottom_half_width - overlap), bottom_z),
                (x, side * (bottom_half_width + thickness), bottom_z),
                (x, side * (top_half_width + thickness), top_z - 2.0),
                (x, side * (top_half_width + thickness - 2.0), top_z),
                (x, side * (top_half_width - overlap), top_z),
            ],
            close=True,
        )
    )


def intake_radial(offset):
    return BODY_RADIUS + offset * INTAKE_HEIGHT_SCALE


def rotate_module(shape, azimuth):
    return shape.rotate(bd.Axis.X, -azimuth)


def style(part, label, color, roughness=0.62, metalness=0.18):
    part.label = label
    part.color = color
    part.cad_material = {"roughness": roughness, "metalness": metalness}
    return part


def make_radome():
    sections = [
        circle_x(NOSE_BASE_X, BODY_RADIUS),
        circle_x(1325.0, 94.0),
        circle_x(1450.0, 75.0),
        circle_x(1560.0, 46.0),
        circle_x(1640.0, 19.0),
        circle_x(HALF_LENGTH, 1.0),
    ]
    return bd.loft(sections, ruled=False)


def make_intake_parts(index, azimuth):
    # The ramp remains body-connected aft of the inlet and presents three
    # deliberate compression breaks inside the open cowl.
    ramp = profile_prism(
        [
            (INTAKE_AFT_X, intake_radial(-2.0)),
            (STRAKE_AFT_X, intake_radial(-0.5)),
            (470.0, intake_radial(5.5)),
            (590.0, intake_radial(11.5)),
            (INTAKE_THROAT_X, intake_radial(19.5)),
            (INTAKE_FRONT_X, intake_radial(11.5)),
            (INTAKE_FRONT_X - 18.0, intake_radial(1.5)),
            (STRAKE_AFT_X, intake_radial(-4.0)),
        ],
        50.0,
    )
    splitter = profile_prism(
        [
            (430.0, intake_radial(-1.0)),
            (690.0, intake_radial(8.0)),
            (INTAKE_FRONT_X, intake_radial(6.0)),
            (INTAKE_FRONT_X - 24.0, intake_radial(1.0)),
            (455.0, intake_radial(-4.0)),
        ],
        64.0,
    )
    ramp = ramp.fuse(splitter)

    # Both cuts overshoot below the outer shells, leaving U-shaped sidewalls
    # and roofs around a real open aperture rather than a framed solid plug.
    lip_outer = loft_trapezoids(
        [
            (INTAKE_FRONT_X - 15.0, intake_radial(10.5), 36.0, intake_radial(57.5), 28.0, INTAKE_FRONT_X),
            (735.0, intake_radial(15.5), 32.0, intake_radial(49.5), 25.0),
        ]
    )
    lip_inner = loft_trapezoids(
        [
            (INTAKE_FRONT_X - 11.0, intake_radial(2.0), 29.0, intake_radial(49.5), 21.0, INTAKE_FRONT_X + 4.0),
            (729.0, intake_radial(4.0), 25.0, intake_radial(42.5), 18.0),
        ]
    )
    lip = lip_outer - lip_inner

    duct_outer_sections = [
        (INTAKE_DUCT_AFT_X, intake_radial(-2.0), 15.0, intake_radial(13.0), 12.0),
        (180.0, intake_radial(0.0), 18.0, intake_radial(19.0), 14.0),
        (360.0, intake_radial(4.0), 22.0, intake_radial(27.0), 17.0),
        (590.0, intake_radial(11.5), 27.0, intake_radial(42.0), 21.0),
        (735.0, intake_radial(15.5), 32.0, intake_radial(49.5), 25.0),
    ]
    duct_outer = loft_trapezoids(duct_outer_sections)
    duct_inner = loft_trapezoids(
        [
            (INTAKE_DUCT_AFT_X - 6.0, intake_radial(-6.0), 11.0, intake_radial(8.0), 8.0),
            (180.0, intake_radial(-5.0), 14.0, intake_radial(14.0), 10.0),
            (360.0, intake_radial(-3.0), 18.0, intake_radial(22.0), 13.0),
            (590.0, intake_radial(1.0), 23.0, intake_radial(36.5), 16.0),
            (739.0, intake_radial(3.0), 28.0, intake_radial(44.5), 20.0),
        ]
    )
    duct = duct_outer - duct_inner

    cheeks = [
        bd.loft(
            [intake_cheek_section(section, side) for section in duct_outer_sections],
            ruled=True,
        )
        for side in (-1.0, 1.0)
    ]

    return [
        style(rotate_module(ramp, azimuth), f"intake_ramp_{index}", FIN_COLOR),
        style(rotate_module(lip, azimuth), f"intake_lip_{index}", HARDWARE_COLOR, 0.42, 0.55),
        style(rotate_module(duct, azimuth), f"intake_duct_{index}", INTAKE_COLOR, 0.78, 0.05),
        *[
            style(
                rotate_module(cheek, azimuth),
                f"intake_cheek_{index}_{side}",
                FIN_COLOR,
            )
            for side, cheek in enumerate(cheeks, 1)
        ],
    ]


def make_booster_fin(index, azimuth):
    shoulder_trailing_x = BOOSTER_FIN_AFT_X + (
        (BOOSTER_FIN_TIP_AFT_X - BOOSTER_FIN_AFT_X)
        * (BOOSTER_FIN_SHOULDER_RADIUS - (BODY_RADIUS - 2.0))
        / (BOOSTER_FIN_RADIUS - (BODY_RADIUS - 2.0))
    )
    fin = aerofoil_loft(
        [
            (BODY_RADIUS - 2.0, BOOSTER_FIN_AFT_X, BOOSTER_FIN_FORWARD_X, 12.0),
            (
                BOOSTER_FIN_SHOULDER_RADIUS,
                shoulder_trailing_x,
                BOOSTER_FIN_SHOULDER_X,
                12.0,
            ),
            (BOOSTER_FIN_RADIUS, BOOSTER_FIN_TIP_AFT_X, BOOSTER_FIN_TIP_FORWARD_X, 8.0),
        ]
    )
    root = root_fairing([
        (BOOSTER_FIN_AFT_X, 12.0, 0.8), (-1470.0, 22.0, 3.5),
        (-1350.0, 26.0, 7.5), (-850.0, 24.0, 7.5),
        (-700.0, 18.0, 2.5), (BOOSTER_FIN_FORWARD_X, 8.0, 0.8),
    ])
    return [
        style(rotate_module(fin, azimuth), f"booster_fin_{index}", FIN_COLOR, 0.56, 0.28),
        style(rotate_module(root, azimuth), f"booster_fin_root_{index}", BOOSTER_COLOR),
    ]


def make_booster_nozzle():
    outer = bd.loft(
        [
            circle_x(-HALF_LENGTH, 94.0),
            circle_x(-1674.0, 98.0),
            circle_x(-1658.0, BODY_RADIUS),
            circle_x(BOOSTER_NOZZLE_START_X, BODY_RADIUS),
        ],
        ruled=True,
    )
    liner_boundary = bd.loft(
        [
            circle_x(-HALF_LENGTH, BOOSTER_NOZZLE_EXIT_RADIUS),
            circle_x(-1668.0, 80.0),
            circle_x(-1645.0, 62.0),
            circle_x(-1605.0, 32.0),
            circle_x(BOOSTER_NOZZLE_THROAT_X, BOOSTER_NOZZLE_THROAT_RADIUS),
            circle_x(-1565.0, 34.0),
            circle_x(-1535.0, 54.0),
            circle_x(BOOSTER_NOZZLE_START_X, BOOSTER_NOZZLE_CHAMBER_RADIUS),
        ],
        ruled=True,
    )
    shell = outer - liner_boundary

    gas_path = bd.loft(
        [
            circle_x(
                -HALF_LENGTH - 1.5,
                BOOSTER_NOZZLE_EXIT_RADIUS - BOOSTER_NOZZLE_LINER_THICKNESS,
            ),
            circle_x(-1668.0, 75.0),
            circle_x(-1645.0, 57.0),
            circle_x(-1605.0, 27.0),
            circle_x(
                BOOSTER_NOZZLE_THROAT_X,
                BOOSTER_NOZZLE_THROAT_RADIUS - BOOSTER_NOZZLE_LINER_THICKNESS,
            ),
            circle_x(-1565.0, 29.0),
            circle_x(-1535.0, 49.0),
            circle_x(
                BOOSTER_NOZZLE_START_X + 1.5,
                BOOSTER_NOZZLE_CHAMBER_RADIUS - BOOSTER_NOZZLE_LINER_THICKNESS,
            ),
        ],
        ruled=True,
    )
    liner = liner_boundary - gas_path

    throat_disk = cylinder_x(
        BOOSTER_NOZZLE_THROAT_X - 1.5,
        BOOSTER_NOZZLE_THROAT_X + 1.5,
        BOOSTER_NOZZLE_THROAT_RADIUS - BOOSTER_NOZZLE_LINER_THICKNESS,
    )

    return [
        style(shell, "booster_nozzle_outer", BOOSTER_COLOR, 0.62, 0.2),
        style(liner, "booster_nozzle_inner", NOZZLE_COLOR, 0.74, 0.2),
        style(throat_disk, "booster_nozzle_recess", INTAKE_COLOR, 0.88, 0.08),
    ]


def make_sustainer_fin(index, azimuth):
    blade = aerofoil_loft(
        [
            (
                BODY_RADIUS - 2.0,
                SUSTAINER_FIN_ROOT_AFT_X + 8.0,
                SUSTAINER_FIN_ROOT_FORWARD_X,
                8.0,
            ),
            (
                SUSTAINER_FIN_RADIUS,
                SUSTAINER_FIN_TIP_AFT_X,
                SUSTAINER_FIN_TIP_FORWARD_X,
                6.0,
            ),
        ]
    )
    root = root_fairing([
        (SUSTAINER_FIN_ROOT_AFT_X, 12.0, 0.8),
        (SUSTAINER_FIN_ROOT_AFT_X + 32.0, 24.0, 10.0),
        (SUSTAINER_FIN_ROOT_FORWARD_X - 40.0, 24.0, 14.0),
        (SUSTAINER_FIN_ROOT_FORWARD_X, 22.0, 10.0),
    ])
    fin = blade.fuse(root)
    return style(
        rotate_module(fin, azimuth),
        f"sustainer_fin_{index}",
        FIN_COLOR,
        0.56,
        0.28,
    )


def make_mounting_hardware():
    rail_start = 180.0 - MOUNT_RAIL_LENGTH * 0.5
    rail_end = 180.0 + MOUNT_RAIL_LENGTH * 0.5
    rail = profile_prism(
        [
            (rail_start, BODY_RADIUS - 1.0),
            (rail_start + 16.0, BODY_RADIUS + 0.6),
            (rail_start + 32.0, BODY_RADIUS + MOUNT_RAIL_HEIGHT),
            (rail_end - 32.0, BODY_RADIUS + MOUNT_RAIL_HEIGHT),
            (rail_end - 16.0, BODY_RADIUS + 0.6),
            (rail_end, BODY_RADIUS - 1.0),
        ],
        MOUNT_RAIL_WIDTH,
    )

    lugs = []
    for index, x in enumerate(MOUNT_LUG_STATIONS, 1):
        half_length = MOUNT_LUG_LENGTH * 0.5
        lug = profile_prism(
            [
                (x - half_length, BODY_RADIUS - 1.0),
                (x - half_length + 7.0, BODY_RADIUS + MOUNT_LUG_HEIGHT),
                (x + half_length - 7.0, BODY_RADIUS + MOUNT_LUG_HEIGHT),
                (x + half_length, BODY_RADIUS - 1.0),
            ],
            MOUNT_LUG_WIDTH,
        )
        # A shallow inset makes the shoe read as hardware without fragile bolts.
        lug -= bd.Box(20.0, 8.0, 2.0).translate(
            (x, 0.0, BODY_RADIUS + MOUNT_LUG_HEIGHT - 0.3), transform=True)
        lugs.append(style(lug, f"suspension_lug_{index}", HARDWARE_COLOR, 0.4, 0.62))

    conduit_start = 380.0 - MOUNT_CONDUIT_LENGTH * 0.5
    conduit_end = 380.0 + MOUNT_CONDUIT_LENGTH * 0.5
    conduit = profile_prism(
        [
            (conduit_start, BODY_RADIUS - 0.6),
            (conduit_start + 12.0, BODY_RADIUS + MOUNT_CONDUIT_HEIGHT),
            (conduit_end - 12.0, BODY_RADIUS + MOUNT_CONDUIT_HEIGHT),
            (conduit_end, BODY_RADIUS - 0.6),
        ],
        MOUNT_CONDUIT_WIDTH,
    ).translate((0.0, 7.0, 0.0), transform=True)

    return [
        style(rail, "dorsal_launch_rail", HARDWARE_COLOR, 0.45, 0.55),
        *lugs,
        style(conduit, "dorsal_wiring_conduit", HARDWARE_COLOR, 0.5, 0.48),
    ]


@step(out="AAM-44_Halberd_Detailed.step")
def halberd_detailed():
    report("upper-stage body")
    parts = [
        style(make_ramjet_body(), "ramjet_body", BODY_COLOR),
        style(
            make_sustainer_nozzle(),
            "sustainer_nozzle",
            SUSTAINER_NOZZLE_COLOR,
            0.4,
            0.62,
        ),
        style(
            tapered_band(SEAM_X + 28.0, SEAM_X + 52.0, BODY_RADIUS, 2.0),
            "stage_joint_band",
            HARDWARE_COLOR,
            0.46,
            0.5,
        ),
        style(
            tapered_band(RAMJET_BAND_X, RAMJET_BAND_X + 22.0, BODY_RADIUS, 1.5),
            "ramjet_joint_band",
            HARDWARE_COLOR,
            0.48,
            0.48,
        ),
        style(
            cylinder_x(RAMJET_BAND_X + 22.0, FORWARD_BAND_X, BODY_RADIUS),
            "forward_body",
            BODY_COLOR,
        ),
        style(
            tapered_band(FORWARD_BAND_X, FORWARD_BAND_X + 24.0, BODY_RADIUS, 1.8),
            "forward_joint_band",
            HARDWARE_COLOR,
            0.48,
            0.48,
        ),
        style(
            panel_ring(cylinder_x(FORWARD_BAND_X + 24.0, NOSE_BASE_X, BODY_RADIUS), NOSE_BASE_X - 8.0),
            "seeker_section",
            BODY_COLOR,
        ),
        style(make_radome(), "radome", RADOME_COLOR, 0.5, 0.08),
    ]

    report("three ramp-intake fin modules")
    for index, azimuth in enumerate(INTAKE_AZIMUTHS, 1):
        parts.extend(make_intake_parts(index, azimuth))
        parts.append(make_sustainer_fin(index, azimuth))

    report("dorsal mounting corridor")
    parts.extend(make_mounting_hardware())

    report("detachable booster and three-fin tail")
    parts.extend(
        [
            style(
                panel_ring(panel_ring(
                    cylinder_x(BOOSTER_NOZZLE_START_X, SEAM_X, BODY_RADIUS),
                    -1490.0), SEAM_X - 62.0),
                "booster_body",
                BOOSTER_COLOR,
                0.72,
                0.18,
            ),
            style(
                tapered_band(SEAM_X - 48.0, SEAM_X, BODY_RADIUS, 3.0, 8.0),
                "booster_forward_collar",
                HARDWARE_COLOR,
                0.48,
                0.5,
            ),
        ]
    )
    parts.extend(make_booster_nozzle())
    for index, azimuth in enumerate(INTAKE_AZIMUTHS, 1):
        parts.extend(make_booster_fin(index, azimuth))

    return bd.Compound(children=parts, label="AAM-44_Halberd_Detailed")


if __name__ == "__main__":
    halberd_detailed()
