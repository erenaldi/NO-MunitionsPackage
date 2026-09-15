"""Compact ADM-160-inspired RDM-9 Phantom exterior, in millimeters.

The missile axis is X with the nose forward. The runtime pivot is at X=0;
+Z is dorsal and +Y is starboard. Public MALD dimensions inform the primary
proportions, while appendages are deliberately compacted to the Phantom's
250 mm carriage envelope.
"""

from cadgen import build123d as bd
from cadgen import srgb


LENGTH = 2800.0
HALF_LENGTH = LENGTH * 0.5
ENVELOPE_RADIUS = 125.0

BODY_WIDTH = 200.0
BODY_HEIGHT = 154.0
NOSE_CAP_WIDTH = 34.0
NOSE_CAP_HEIGHT = 28.0
APPENDAGE_RADIUS = 123.5
NOZZLE_INNER_RADIUS = 47.0

BODY_COLOR = srgb("#8F989B")
NOSE_COLOR = srgb("#A8AFB0")
RF_PANEL_COLOR = srgb("#C1B7A9")
FIN_COLOR = srgb("#707A7D")
INTAKE_COLOR = srgb("#22282A")
NOZZLE_COLOR = srgb("#40474A")
RECESS_COLOR = srgb("#15191A")


def section_wire(x, width, height, top_ratio=0.35, bottom_ratio=0.42):
    """Eight-sided MALD-like fuselage section normal to X."""
    half_width = width * 0.5
    half_height = height * 0.5
    return bd.Wire.make_polygon(
        [
            (x, -width * top_ratio, half_height),
            (x, width * top_ratio, half_height),
            (x, half_width, height * 0.25),
            (x, half_width, -height * 0.25),
            (x, width * bottom_ratio, -half_height),
            (x, -width * bottom_ratio, -half_height),
            (x, -half_width, -height * 0.25),
            (x, -half_width, height * 0.25),
        ],
        close=True,
    )


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


def profile_prism_xz(points, width, y_center=0.0):
    wire = bd.Wire.make_polygon(
        [(x, y_center - width * 0.5, z) for x, z in points],
        close=True,
    )
    return bd.Solid.extrude(bd.Face(wire), (0.0, width, 0.0))


def plate_from_xy(points, z_min, thickness):
    wire = bd.Wire.make_polygon([(x, y, z_min) for x, y in points], close=True)
    return bd.Solid.extrude(bd.Face(wire), (0.0, 0.0, thickness))


def side_panel(side):
    y_inner = side * 98.0
    points = [
        (60.0, y_inner, -42.0),
        (100.0, y_inner, -52.0),
        (540.0, y_inner, -52.0),
        (580.0, y_inner, -42.0),
        (580.0, y_inner, 42.0),
        (540.0, y_inner, 52.0),
        (100.0, y_inner, 52.0),
        (60.0, y_inner, 42.0),
    ]
    return bd.Solid.extrude(bd.Face(bd.Wire.make_polygon(points, close=True)), (0.0, side * 5.0, 0.0))


def horizontal_fin(side, root_aft, root_front, tip_aft, tip_front, z_center):
    root_y = side * 96.0
    tip_y = side * APPENDAGE_RADIUS
    points = [
        (root_aft, root_y),
        (root_front, root_y),
        (tip_front, tip_y),
        (tip_aft, tip_y),
    ]
    if side < 0.0:
        points.reverse()
    return plate_from_xy(points, z_center - 3.0, 6.0)


def vertical_fin(points, width=6.0):
    return profile_prism_xz(points, width)


def style(part, label, color, roughness=0.64, metalness=0.18):
    part.label = label
    part.color = color
    part.cad_material = {"roughness": roughness, "metalness": metalness}
    return part


def make_body():
    body = bd.Solid.make_loft(
        [
            section_wire(-HALF_LENGTH, 142.0, 112.0),
            section_wire(-1375.0, 142.0, 112.0),
            section_wire(-1250.0, 176.0, 142.0),
            section_wire(-1050.0, BODY_WIDTH, BODY_HEIGHT),
            section_wire(900.0, BODY_WIDTH, BODY_HEIGHT),
            section_wire(1080.0, 188.0, 146.0),
            section_wire(1240.0, 126.0, 100.0),
            section_wire(1340.0, 62.0, 48.0),
            section_wire(1380.0, 40.0, 32.0),
            section_wire(HALF_LENGTH, NOSE_CAP_WIDTH, NOSE_CAP_HEIGHT),
        ],
        ruled=True,
    )
    cavity = cylinder_x(-HALF_LENGTH - 1.0, -1335.0, NOZZLE_INNER_RADIUS)
    return body - cavity


def make_intake_cowl():
    roof = profile_prism_xz(
        [(105.0, 77.0), (155.0, 96.0), (445.0, 122.0),
         (490.0, 120.0), (490.0, 114.0), (165.0, 90.0), (120.0, 77.0)],
        40.0,
    )
    cheek_profile = [
        (112.0, 76.0), (158.0, 94.0), (486.0, 119.0),
        (486.0, 91.0), (165.0, 86.0), (125.0, 76.0),
    ]
    port = profile_prism_xz(cheek_profile, 5.0, -17.5)
    starboard = profile_prism_xz(cheek_profile, 5.0, 17.5)
    return roof.fuse(port, starboard)


def make_phantom_mald_hybrid():
    body = make_body()
    parts = [
        style(body, "faceted_body", BODY_COLOR),
        style(side_panel(-1.0), "rf_panel_port", RF_PANEL_COLOR, 0.5, 0.12),
        style(side_panel(1.0), "rf_panel_starboard", RF_PANEL_COLOR, 0.5, 0.12),
        style(make_intake_cowl(), "dorsal_intake_cowl", FIN_COLOR, 0.55, 0.24),
        style(
            profile_prism_xz([(125.0, 76.0), (475.0, 88.0), (475.0, 94.0), (150.0, 82.0)], 30.0),
            "dorsal_intake_recess",
            INTAKE_COLOR,
            0.86,
            0.05,
        ),
        style(horizontal_fin(-1.0, -700.0, -100.0, -530.0, -240.0, 0.0), "midwing_port", FIN_COLOR),
        style(horizontal_fin(1.0, -700.0, -100.0, -530.0, -240.0, 0.0), "midwing_starboard", FIN_COLOR),
        style(horizontal_fin(-1.0, -1280.0, -760.0, -1160.0, -900.0, 0.0), "tailplane_port", FIN_COLOR),
        style(horizontal_fin(1.0, -1280.0, -760.0, -1160.0, -900.0, 0.0), "tailplane_starboard", FIN_COLOR),
        style(
            vertical_fin([(-1280.0, 52.0), (-730.0, 77.0), (-900.0, APPENDAGE_RADIUS), (-1180.0, APPENDAGE_RADIUS)]),
            "dorsal_fin",
            FIN_COLOR,
        ),
        style(
            vertical_fin([(-1260.0, -52.0), (-850.0, -77.0), (-990.0, -APPENDAGE_RADIUS), (-1170.0, -APPENDAGE_RADIUS)]),
            "ventral_keel",
            FIN_COLOR,
        ),
        style(annular_cylinder_x(-1400.0, -1382.0, 60.0, NOZZLE_INNER_RADIUS), "nozzle_lip", NOZZLE_COLOR, 0.5, 0.34),
        style(cylinder_x(-1340.0, -1335.0, NOZZLE_INNER_RADIUS), "nozzle_recess", RECESS_COLOR, 0.88, 0.04),
    ]
    return bd.Compound(children=parts, label="RDM-9_Phantom_MALD_Hybrid")
