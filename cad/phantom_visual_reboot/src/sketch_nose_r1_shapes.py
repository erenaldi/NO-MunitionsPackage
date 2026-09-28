"""One reversible sketch-led RDM-9 study. mm; +X nose, +Z dorsal.

The inline front/bottom sketch is interpreted as a lightly rounded-square
main section leading into a pointed, lower-V-chined planar nose. This is a
concept prototype, not a photogrammetric reconstruction of the sketch.
"""

import math

from cadgen import build123d as bd, srgb


LENGTH = 2800.0
BODY_SIDE = 172.0
CORNER_RADIUS = 10.0
WING_HINGE_X = -120.0
WING_HINGE_Y = 14.0
WING_Z = 87.0
TAIL_HINGE_RADIUS = 108.0
TAIL_SPAN = 42.0


def tag(part, label, color="#A7B4BC"):
    part.label = label
    part.color = srgb(color)
    return part


def square_section(x, side, radius):
    return bd.RectangleRounded(side, side, radius).rotate(bd.Axis.Y, 90).translate((x, 0, 0))


def nose_profile(x, width, top, lower_side, keel, corner):
    """Ten aligned polygon vertices preserve a physical ventral ridge."""
    y = width / 2
    yz = ((0, top), (y-corner, top), (y, top-corner),
          (y, lower_side+corner), (y-corner, lower_side),
          (0, keel), (-y+corner, lower_side), (-y, lower_side+corner),
          (-y, top-corner), (-y+corner, top))
    return bd.Wire.make_polygon([(x, yy, zz) for yy, zz in yz], close=True)


def body():
    # Repeated identical rounded-square wires yield true cylindrical corner
    # arcs through the midbody, rather than the eight planar chamfers of A/B/C.
    hull = bd.loft([
        square_section(-1400, 154, 10),
        square_section(-1260, BODY_SIDE, CORNER_RADIUS),
        square_section(900, BODY_SIDE, CORNER_RADIUS),
    ], ruled=True)
    # Start inside the square body's final millimetre. The nose is deliberately
    # faceted and has a bottom V/chine; a finite tiny cap avoids a bad STEP
    # vertex singularity while the planform still reads as pointed.
    wedge = bd.Solid.make_loft([
        nose_profile(899, 170, 84, -75, -85, 10),
        nose_profile(1160, 90, 53, -39, -64, 6),
        # High apex: front projection makes a Y below the nearly flat roof
        # instead of crossing all four corners through a center-height tip.
        nose_profile(1400, 1.2, 42, 39, 38, .2),
    ], ruled=True)
    exterior = hull + wedge
    bore = bd.Cylinder(29., 56., align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    bore = bore.rotate(bd.Axis.Y, 90).translate((-1401., 0, 0))
    return tag(exterior - bore, "square_body_chined_nose")


def panel(side):
    sign = 1 if side == "starboard" else -1
    root, tip = WING_HINGE_Y*sign, (WING_HINGE_Y+505.)*sign
    outline = [(WING_HINGE_X-65, root), (WING_HINGE_X+65, root),
               (WING_HINGE_X+38, tip), (WING_HINGE_X-31, tip)]
    wire = bd.Wire.make_polygon([(x, y, WING_Z) for x, y in outline], close=True)
    return bd.extrude(bd.Face(wire), amount=3.)


def wing(side, state):
    part = panel(side)
    if state == "stowed":
        hinge = bd.Axis((WING_HINGE_X, WING_HINGE_Y if side == "starboard" else -WING_HINGE_Y, 0), (0, 0, 1))
        part = part.rotate(hinge, -90.)
    return tag(part, "wing_" + side, "#8498A0")


def fin(angle, state):
    theta = math.radians(angle)
    ry, rz = math.sin(theta), math.cos(theta)
    ty, tz = math.cos(theta), -math.sin(theta)
    coords = ((-1264, 0), (-1055, 0), (-1128, TAIL_SPAN),
              (-1242, TAIL_SPAN*.82))
    profiles = []
    for thickness in (-1.65, 1.65):
        profiles.append(bd.Wire.make_polygon([
            (x, ry*(TAIL_HINGE_RADIUS+r)+ty*thickness,
             rz*(TAIL_HINGE_RADIUS+r)+tz*thickness)
            for x, r in coords], close=True))
    part = bd.Solid.make_loft(profiles, ruled=True)
    if state == "stowed":
        hinge = bd.Axis((0, TAIL_HINGE_RADIUS*ry, TAIL_HINGE_RADIUS*rz), (1, 0, 0))
        part = part.rotate(hinge, 90. if ry*rz > 0 else -90.)
    return tag(part, "tail_fin_%03d" % angle, "#8A969B")


def build(state):
    if state not in ("deployed", "stowed"):
        raise ValueError(state)
    parts = [body()]
    for side, sign in (("port", -1), ("starboard", 1)):
        parts.append(tag(bd.Box(255, 2, 15).translate((525, sign*(BODY_SIDE/2-2.5), 0)),
                         "flush_rf_" + side, "#72858A"))
        parts.append(tag(bd.Box(46, 29, 24).translate((WING_HINGE_X, sign*WING_HINGE_Y, 81)),
                         "hinge_seat_" + side, "#697D85"))
        parts.append(wing(side, state))
    parts.extend(fin(angle, state) for angle in (45, 135, 225, 315))
    return bd.Compound(children=parts, label="RDM9_D_SketchNose_R1_" + state)


def section_slab(x):
    width = 8.0
    blade = bd.Box(width, 360, 360).translate((x, 0, 0))
    return tag(body() & blade, "nose_section" if x > 900 else "rounded_square_midsection")
