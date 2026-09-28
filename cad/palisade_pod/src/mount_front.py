"""Reference-led Palisade mount-front fairing; only the forward A2 end changes."""

import math

from cadgen import build123d as bd

from housing import cassettes, housing, solid_box


def rounded_section(x, width, height, corner_radius, center_z=-111.5):
    """Rounded rectangle in a +X section plane, with identical vertex clocks."""
    half_w, half_h = width/2, height/2
    points = []
    for cy, cz, angle in ((half_w-corner_radius, half_h-corner_radius, 0),
                          (-half_w+corner_radius, half_h-corner_radius, 90),
                          (-half_w+corner_radius, -half_h+corner_radius, 180),
                          (half_w-corner_radius, -half_h+corner_radius, 270)):
        for i in range(5):
            theta = math.radians(angle+i*90/4)
            points.append((x, cy+corner_radius*math.cos(theta),
                           center_z+cz+corner_radius*math.sin(theta)))
    return bd.Wire.make_polygon(points, close=True)


def front_fairing():
    stations = ((1325., 400., 223., 20.), (1360., 400., 223., 25.),
                (1420., 370., 211., 34.), (1460., 310., 189., 42.),
                (1490., 270., 165., 50.))
    fairing = bd.Solid.make_loft(
        [rounded_section(*station) for station in stations], ruled=True)
    fairing -= solid_box("forward_recess_tool", 8, 110, 36, (1491, 0, -113))
    fairing.label = "forward_sensor_shell"
    return fairing


def study(filled):
    frame = [part for part in housing()
             if not part.label.endswith("_outer_rail") and
             part.label != "forward_sensor_shell"]
    frame.append(front_fairing())
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
