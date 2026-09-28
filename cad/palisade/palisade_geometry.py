"""HKP-1 Palisade interceptor silhouette candidate, in millimeters.

The interceptor axis is X with the nose forward and the assembly centered on
the runtime pivot at X=0. +Z is dorsal and +Y is starboard. The aft turning
cap is a separate solid so the concealed main nozzle at the body/cap
interface is exposed when the cap is removed. Silhouette level only: no
tertiary detail, no Unity export.
"""

import math

from cadgen import build123d as bd
from cadgen import srgb


LENGTH = 1200.0
HALF_LENGTH = LENGTH * 0.5
BODY_RADIUS = 70.0
NOSE_RADIUS = 70.0
CAP_LENGTH = 170.0
BODY_AFT = -HALF_LENGTH + CAP_LENGTH  # -430.0, body/cap interface
BODY_FWD = HALF_LENGTH - NOSE_RADIUS  # 530.0

CAVITY_RADIUS = 45.0
CAVITY_DEPTH = 55.0
LIP_OUTER_RADIUS = 45.0
LIP_INNER_RADIUS = 32.0
LIP_LENGTH = 4.0
CONE_AFT_RADIUS = 32.5
CONE_FWD_RADIUS = 18.0
CONE_LENGTH = 46.5

STAB_ANGLES = (45.0, 135.0, 225.0, 315.0)
STAB_ROOT_AFT = -420.0
STAB_ROOT_FWD = -370.0
STAB_TIP_X = -395.0
STAB_TIP_RADIUS = 82.0
STAB_THICKNESS = 3.0

NOZZLE_ANGLES = (0.0, 90.0, 180.0, 270.0)
NOZZLE_RADIUS = 11.0
NOZZLE_LENGTH = 12.0
NOZZLE_X = -520.0
NOZZLE_CENTER_RADIUS = BODY_RADIUS + NOZZLE_LENGTH * 0.5

ENVELOPE_RADIUS = 85.0

BODY_COLOR = srgb("#8F989B")
CAP_COLOR = srgb("#A8AFB0")
STAB_COLOR = srgb("#707A7D")
MAIN_NOZZLE_COLOR = srgb("#15191A")
CAP_NOZZLE_COLOR = srgb("#40474A")


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


def cone_x(x_min, x_max, r_min, r_max):
    return (
        bd.Cone(r_min, r_max, x_max - x_min, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        .rotate(bd.Axis.Y, 90.0)
        .translate((x_min, 0.0, 0.0), transform=True)
    )


def style(part, label, color, roughness=0.64, metalness=0.18):
    part.label = label
    part.color = color
    part.cad_material = {"roughness": roughness, "metalness": metalness}
    return part


def circle_wire(x, radius):
    return bd.Wire.make_circle(
        radius, bd.Plane(origin=(x, 0.0, 0.0), x_dir=(0.0, 1.0, 0.0), z_dir=(1.0, 0.0))
    )


def make_body():
    sections = [
        circle_wire(x, BODY_RADIUS)
        for x in (-430.0, -300.0, -150.0, 0.0, 150.0, 300.0, 450.0, BODY_FWD)
    ]
    for dx in (15.0, 30.0, 45.0, 55.0, 63.0, 68.0):
        sections.append(circle_wire(BODY_FWD + dx, math.sqrt(NOSE_RADIUS**2 - dx**2)))
    sections.append(bd.Vertex((HALF_LENGTH, 0.0, 0.0)))
    body = bd.Solid.make_loft(sections, ruled=True)
    cavity = cylinder_x(BODY_AFT, BODY_AFT + CAVITY_DEPTH, CAVITY_RADIUS)
    return body - cavity


def make_cap():
    return cylinder_x(-HALF_LENGTH, BODY_AFT, BODY_RADIUS)


def make_main_nozzle():
    lip = annular_cylinder_x(BODY_AFT, BODY_AFT + LIP_LENGTH, LIP_OUTER_RADIUS, LIP_INNER_RADIUS)
    cone = cone_x(BODY_AFT + LIP_LENGTH - 0.5, BODY_AFT + LIP_LENGTH - 0.5 + CONE_LENGTH, CONE_AFT_RADIUS, CONE_FWD_RADIUS)
    return lip.fuse(cone)


def make_stabilizer(angle_deg):
    a = math.radians(angle_deg)
    radial = (0.0, math.cos(a), math.sin(a))
    tangential = (0.0, -math.sin(a), math.cos(a))
    points = [
        (STAB_ROOT_AFT, BODY_RADIUS),
        (STAB_ROOT_FWD, BODY_RADIUS),
        (STAB_TIP_X, STAB_TIP_RADIUS),
    ]
    wire = bd.Wire.make_polygon(
        [(x, r * radial[1], r * radial[2]) for x, r in points],
        close=True,
    )
    return bd.Solid.extrude(
        bd.Face(wire),
        (0.0, tangential[1] * STAB_THICKNESS, tangential[2] * STAB_THICKNESS),
    )


def make_cap_nozzle(angle_deg):
    a = math.radians(angle_deg)
    radial = (0.0, math.cos(a), math.sin(a))
    outer = bd.Cylinder(
        NOZZLE_RADIUS, NOZZLE_LENGTH,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER),
    )
    inner = bd.Cylinder(
        NOZZLE_RADIUS * 0.55, NOZZLE_LENGTH + 1.0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER),
    )
    nozzle = outer - inner
    nozzle = nozzle.rotate(bd.Axis.X, 90.0 - angle_deg)
    return nozzle.translate(
        (NOZZLE_X, NOZZLE_CENTER_RADIUS * radial[1], NOZZLE_CENTER_RADIUS * radial[2])
    )


def make_palisade_interceptor():
    parts = [
        style(make_body(), "body", BODY_COLOR),
        style(make_cap(), "turning_cap", CAP_COLOR),
        style(make_main_nozzle(), "main_nozzle", MAIN_NOZZLE_COLOR, 0.88, 0.04),
    ]
    for angle in STAB_ANGLES:
        parts.append(style(make_stabilizer(angle), f"stabilizer_{int(round(angle))}", STAB_COLOR))
    for angle in NOZZLE_ANGLES:
        parts.append(style(make_cap_nozzle(angle), f"nozzle_{int(round(angle))}", CAP_NOZZLE_COLOR))
    return bd.Compound(children=parts, label="HKP-1_Palisade_Interceptor")
