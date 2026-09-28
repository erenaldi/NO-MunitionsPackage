"""PAC-3-inspired recessed ACM visual band around the whole Spear cap."""

import math

from cadgen import build123d as bd

from concept_shapes import SEPARATION, tag
from spear_acm_port_shapes import BACK_RADIAL, BORE_RADIUS, cylinder, radial
from spear_cylinder_cap_shapes import cylindrical_cap
from spear_uniform_barrel_shapes import AFT, BARREL_RADIUS, NEW_SEAM, make_uniform_spear


ROWS_X = (-568., -550., -532., -514., -496., -478.)
PORTS_PER_ROW = 16
AZIMUTH_PITCH = 360. / PORTS_PER_ROW
STAGGER = AZIMUTH_PITCH/2


def stations():
    return tuple((row, column, x, column*AZIMUTH_PITCH+(row%2)*STAGGER)
                 for row, x in enumerate(ROWS_X)
                 for column in range(PORTS_PER_ROW))


def perforated_cap(points):
    raw = cylindrical_cap(radius=BARREL_RADIUS, aft=AFT, forward=NEW_SEAM,
                          socket_x=None)
    tool = cylinder(BORE_RADIUS, 13.)
    cutters = bd.Compound(children=[radial(tool, x, theta, BACK_RADIAL)
                                    for _, _, x, theta in points])
    return tag(raw-cutters, "turning_cap", "#949EA3")


def inserts(points):
    annulus = cylinder(4.75, 5.) - cylinder(3.25, 5.5)
    dark_center = cylinder(3.2, 4.6)
    parts = []
    for row, column, x, theta in points:
        parts.append(tag(radial(annulus, x, theta, BACK_RADIAL),
                         f"acm_rim_{row}_{column}", "#30383B"))
        parts.append(tag(radial(dark_center, x, theta, BACK_RADIAL),
                         f"acm_core_{row}_{column}", "#11171B"))
    return parts


def make_full_acm_pattern(separated=False, cap_only=False):
    points = stations()
    old = make_uniform_spear()
    parts = [perforated_cap(points) if item.label == "turning_cap" else item
             for item in old.children if not item.label.startswith("thruster_")]
    parts.extend(inserts(points))
    if cap_only:
        parts = [part for part in parts
                 if part.label == "turning_cap" or part.label.startswith("acm_")]
    elif separated:
        parts = [part.moved(bd.Location((-SEPARATION, 0, 0)))
                 if part.label == "turning_cap" or part.label.startswith("acm_")
                 else part for part in parts]
    suffix = "_Cap_Focus" if cap_only else ("_Separated" if separated else "")
    return bd.Compound(children=parts, label=f"Spear_ACMWrap{suffix}")
