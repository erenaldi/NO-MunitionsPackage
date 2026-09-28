"""Shared RDM-9 Phantom exterior geometry, in millimeters.

The missile axis is X with the nose forward. The runtime pivot is at the
midpoint, X=0; +Z is dorsal and +Y is lateral.
"""

from cadgen import build123d as bd
from cadgen import srgb


LENGTH = 2800.0
HALF_LENGTH = LENGTH * 0.5
BODY_RADIUS = 112.5
ENVELOPE_RADIUS = 125.0

LENS_SHOULDER_LENGTH = 32.0
NOZZLE_MOUTH_X = -HALF_LENGTH
NOZZLE_LIP_END_X = -1384.0
NOZZLE_CAVITY_END_X = -1355.0
NOZZLE_OUTER_RADIUS = 92.0
NOZZLE_INNER_RADIUS = 72.0

BODY_COLOR = srgb("#929A9C")
LENS_COLOR = srgb("#D0D5D3")
NOZZLE_LIP_COLOR = srgb("#454B4E")
NOZZLE_RECESS_COLOR = srgb("#171B1D")


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


def style(part, label, color, roughness, metalness):
    part.label = label
    part.color = color
    part.cad_material = {"roughness": roughness, "metalness": metalness}
    return part


def make_body():
    # Closely spaced forward stations soften the nose without exceeding the
    # fixed radius; the shallow aft taper leaves room for the recessed nozzle.
    body = bd.loft(
        [
            circle_x(-1388.0, 92.0),
            circle_x(-1360.0, 108.0),
            circle_x(-1325.0, BODY_RADIUS),
            circle_x(1120.0, BODY_RADIUS),
            circle_x(1180.0, 110.0),
            circle_x(1240.0, 102.0),
            circle_x(1300.0, 88.0),
            circle_x(1350.0, 67.0),
            circle_x(1380.0, 42.0),
            circle_x(1395.0, 20.0),
            circle_x(HALF_LENGTH, 4.0),
        ],
        ruled=True,
    )
    cavity = cylinder_x(NOZZLE_MOUTH_X - 1.0, NOZZLE_CAVITY_END_X, NOZZLE_INNER_RADIUS)
    return body - cavity


def make_lens_housing(width):
    half_width = width * 0.5
    outer = bd.loft(
        [
            circle_x(-half_width, BODY_RADIUS),
            circle_x(-half_width + LENS_SHOULDER_LENGTH, ENVELOPE_RADIUS),
            circle_x(half_width - LENS_SHOULDER_LENGTH, ENVELOPE_RADIUS),
            circle_x(half_width, BODY_RADIUS),
        ],
        ruled=True,
    )
    # One millimeter of radial seating guarantees body contact after STEP export.
    return outer - cylinder_x(-half_width - 1.0, half_width + 1.0, BODY_RADIUS - 1.0)


def make_nozzle_lip():
    return annular_cylinder_x(
        NOZZLE_MOUTH_X,
        NOZZLE_LIP_END_X,
        NOZZLE_OUTER_RADIUS,
        NOZZLE_INNER_RADIUS,
    )


def make_nozzle_recess():
    # Closed dark backing only: the cavity is visual and contains no engine internals.
    return cylinder_x(-1360.0, NOZZLE_CAVITY_END_X, NOZZLE_INNER_RADIUS)


def make_phantom(lens_width):
    if lens_width <= 2.0 * LENS_SHOULDER_LENGTH:
        raise ValueError("Lens width must leave room for both rounded shoulders")

    parts = [
        style(make_body(), "body", BODY_COLOR, 0.68, 0.16),
        style(make_lens_housing(lens_width), "lens_housing", LENS_COLOR, 0.44, 0.24),
        style(make_nozzle_lip(), "nozzle_lip", NOZZLE_LIP_COLOR, 0.54, 0.32),
        style(make_nozzle_recess(), "nozzle_recess", NOZZLE_RECESS_COLOR, 0.86, 0.06),
    ]
    return bd.Compound(
        children=parts,
        label=f"RDM-9_Phantom_Lens{int(lens_width)}",
    )
