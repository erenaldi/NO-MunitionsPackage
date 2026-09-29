"""A10 silhouette: wedge nose with level belly and stubbier level rear tip.

User direction (2026-09-28, after the 1.2x nodding nose): the underside of
the forward fairing must stay as horizontal as the drawing - flush with the
beam underside at -223 - while the A9-style roof curve carries the whole
droop to a tip seated at the belly line. The rear only becomes slightly
stubbier and stays level. Dimensions are millimetres.
"""

import math

from cadgen import build123d as bd

from continuous_ends import section
from housing import cassettes, housing, solid_box

FRONT_ROOT, FRONT_TIP = 1325., 1883.
AFT_ROOT, AFT_TIP = -1325., -1670.
ROOF_DROP_MM = 211.
VALUES = (0., .02, .08, .16, .28, .4, .52, .64, .75, .84, .9, .95,
          .98, .995, 1.)


def level_fairing(root, tip, label):
    """A9 rear profile: level centre, sqrt(1-t^2) section collapse."""
    wires = []
    for t in (VALUES if tip > root else tuple(reversed(VALUES))):
        x = root+(tip-root)*t
        scale = math.sqrt(max(0., 1-t*t))
        if t <= .02:
            scale = 1.
        if t == 1.:
            width, height, radius = 8., 4., 1.7
        else:
            width = 399.9*scale
            height = 223. if t == 0. else 222.9*scale
            radius = 12+(.45*height-12)*(t**1.5)
        wires.append(section(x, width, height, radius))
    shape = bd.Solid.make_loft(wires, ruled=False)
    shape.label = label
    return shape


def wedge_fairing(root, tip, label):
    """Teal-dome nose: belly flush at -223, roof holds high then dives.

    The roof follows -drop*t^3 so it stays near the beam top through the
    first stretch, descends gently through the middle, and steepens toward
    a blunt 24x12 tip rounded into the flat belly line.
    """
    wires = []
    for t in VALUES:
        x = root+(tip-root)*t
        scale = math.sqrt(max(0., 1-t*t))
        if t <= .02:
            scale = 1.
        if t == 1.:
            width, height, radius = 24., 12., 5.4
            centre_z = -217.
        else:
            width = 399.9*scale
            roof = -ROOF_DROP_MM*(t**3)
            belly = -223.
            height = roof-belly
            centre_z = (roof+belly)/2
            radius = 12+(.45*height-12)*(t**1.5)
        wires.append(section(x, width, height, radius, centre_z))
    shape = bd.Solid.make_loft(wires, ruled=False)
    shape.label = label
    return shape


def study(filled):
    frame = [part for part in housing() if part.label not in (
        "forward_sensor_shell", "aft_sensor_shell", "forward_aperture",
        "aft_aperture", "port_outer_rail", "starboard_outer_rail")]
    frame.extend((wedge_fairing(FRONT_ROOT, FRONT_TIP, "forward_sensor_shell"),
                  level_fairing(AFT_ROOT, AFT_TIP, "aft_sensor_shell")))
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
