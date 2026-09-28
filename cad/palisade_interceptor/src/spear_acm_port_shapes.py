"""One reference-led, six-port lateral ACM group on selected Spear cap."""

import math

from cadgen import build123d as bd

from concept_shapes import SEPARATION, tag
from spear_cylinder_cap_shapes import cylindrical_cap
from spear_uniform_barrel_shapes import AFT, BARREL_RADIUS, NEW_SEAM, make_uniform_spear


AXIAL_X = (-549., -535., -521.)
ROW_ANGLES = (-8., 8.)
BORE_RADIUS = 5.3
BACK_RADIAL = BARREL_RADIUS-7.


def radial(shape, x, theta, start_radius):
    angle = math.radians(theta)
    return shape.rotate(bd.Axis.X, theta-90.).translate(
        (x, start_radius*math.cos(angle), start_radius*math.sin(angle)))


def cylinder(radius, depth):
    return bd.Cylinder(radius, depth,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def port_stations():
    return tuple((index, x, theta) for index, (x, theta) in enumerate(
        (point for x in AXIAL_X for point in ((x, ROW_ANGLES[0]), (x, ROW_ANGLES[1])))))


def cap_with_one_group():
    cap = cylindrical_cap(radius=BARREL_RADIUS, aft=AFT, forward=NEW_SEAM,
                          socket_x=None)
    for _, x, theta in port_stations():
        drill = radial(cylinder(BORE_RADIUS, 13.), x, theta, BACK_RADIAL)
        cap = cap-drill
    return tag(cap, "turning_cap", "#949EA3")


def port_inserts(index, x, theta):
    outside = cylinder(4.75, 5.)
    inside = cylinder(3.25, 5.5)
    rim = radial(outside-inside, x, theta, BACK_RADIAL)
    core = radial(cylinder(3.2, 4.6), x, theta, BACK_RADIAL)
    return (tag(rim, f"acm_0_rim_{index}", "#30383B"),
            tag(core, f"acm_0_core_{index}", "#11171B"))


def make_acm_group_preview(separated=False, cap_only=False):
    baseline = make_uniform_spear()
    parts = [cap_with_one_group() if item.label == "turning_cap" else item
             for item in baseline.children
             if item.label not in ("thruster_0", "thruster_0_throat")]
    for station in port_stations():
        parts.extend(port_inserts(*station))
    if cap_only:
        parts = [item for item in parts
                 if item.label == "turning_cap" or item.label.startswith(("thruster_", "acm_"))]
    elif separated:
        parts = [item.moved(bd.Location((-SEPARATION, 0, 0)))
                 if item.label == "turning_cap" or item.label.startswith(("thruster_", "acm_"))
                 else item for item in parts]
    suffix = "_Cap_Focus" if cap_only else ("_Separated" if separated else "")
    return bd.Compound(children=parts, label=f"Spear_ACMPortGroup0{suffix}")
