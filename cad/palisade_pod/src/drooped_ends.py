"""A10 silhouette: A9-slope nodding nose and stubbier level rear tip.

User direction (2026-09-28, after A10-v1): the forward end keeps the A9
teardrop profile and slope, but its vertical-tangent tip point sits lower
than the beam's halfway height; the rear only becomes slightly stubbier and
stays level. Section collapse keeps the proven A9 sqrt(1-t^2) law while the
section centre sinks by drop*t^2, so the root stays tangent to the beam roof
and no belly rebound appears. Dimensions are millimetres.
"""

import math

from cadgen import build123d as bd

from continuous_ends import section
from housing import cassettes, housing, solid_box

FRONT_ROOT, FRONT_TIP = 1325., 2255.
AFT_ROOT, AFT_TIP = -1325., -1670.
FRONT_DROP_MM = 60.
VALUES = (0., .02, .08, .16, .28, .4, .52, .64, .75, .84, .9, .95,
          .98, .995, 1.)


def fairing(root, tip, label, drop=0.):
    """A9 teardrop profile; drop>0 sinks the tip point by drop*t^2 mm."""
    wires = []
    for t in (VALUES if tip > root else tuple(reversed(VALUES))):
        x = root+(tip-root)*t
        scale = math.sqrt(max(0., 1-t*t))
        if t <= .02:
            scale = 1.
        centre_z = -111.5-drop*t*t
        if t == 1.:
            width, height, radius = 8., 4., 1.7
        else:
            width = 399.9*scale
            height = 223. if t == 0. else 222.9*scale
            radius = 12+(.45*height-12)*(t**1.5)
        wires.append(section(x, width, height, radius, centre_z))
    shape = bd.Solid.make_loft(wires, ruled=False)
    shape.label = label
    return shape


def study(filled):
    frame = [part for part in housing() if part.label not in (
        "forward_sensor_shell", "aft_sensor_shell", "forward_aperture",
        "aft_aperture", "port_outer_rail", "starboard_outer_rail")]
    frame.extend((fairing(FRONT_ROOT, FRONT_TIP, "forward_sensor_shell",
                          FRONT_DROP_MM),
                  fairing(AFT_ROOT, AFT_TIP, "aft_sensor_shell")))
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
