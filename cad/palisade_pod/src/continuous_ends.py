"""A9 silhouette-only continuous ends: no terminal sensor apertures yet.

The user-directed side envelope is a level beam with a longer forward and a
shorter aft rounded tip. Rounded rectangular sections keep a broad root
interface while converging toward near-point tips. Dimensions are mm.
"""

import math

from cadgen import build123d as bd

from housing import cassettes, housing, solid_box


def section(x, width, height, corner_radius, centre_z=-111.5):
    """Clock-stable rounded rectangle, 36 perimeter vertices in a +X plane."""
    half_y, half_z = width/2, height/2
    radius = min(corner_radius, half_y*.96, half_z*.96)
    vertices = []
    for cy, cz, angle in ((half_y-radius, half_z-radius, 0),
                          (-half_y+radius, half_z-radius, 90),
                          (-half_y+radius, -half_z+radius, 180),
                          (half_y-radius, -half_z+radius, 270)):
        for j in range(9):
            theta = math.radians(angle+j*90/8)
            vertices.append((x, cy+radius*math.cos(theta),
                             centre_z+cz+radius*math.sin(theta)))
    return bd.Wire.make_polygon(vertices, close=True)


def fairing(root, tip, label):
    # Cosine-like/elliptic side transition: level tangent at the beam root,
    # strongly rounded at the extremity. A second full-width root station
    # controls spline tangency so the loft cannot grow a shoulder hump.
    values = (0., .02, .08, .16, .28, .4, .52, .64, .75, .84, .9, .95,
              .98, .995, 1.)
    wires = []
    for t in (values if tip > root else tuple(reversed(values))):
        x = root+(tip-root)*t
        scale = math.sqrt(max(0., 1-t*t))
        if t <= .02:
            scale = 1.
        if t == 1.:
            width, height, radius = 8., 4., 1.7
        else:
            # Allow 0.1 mm for the native smooth loft's small interpolation
            # overshoot near the square root. The central A2 skin remains 400.
            width = 399.9*scale
            height = 223. if t == 0. else 222.9*scale
            radius = 12+(.45*height-12)*(t**1.5)
        wires.append(section(x, width, height, radius))
    shape = bd.Solid.make_loft(wires, ruled=False)
    shape.label = label
    return shape


def study(filled):
    frame = [part for part in housing() if part.label not in (
        "forward_sensor_shell", "aft_sensor_shell", "forward_aperture",
        "aft_aperture", "port_outer_rail", "starboard_outer_rail")]
    frame.extend((fairing(1325, 1790, "forward_sensor_shell"),
                  fairing(-1325, -1710, "aft_sensor_shell")))
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
