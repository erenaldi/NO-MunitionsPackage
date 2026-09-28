"""A plain Spear cap cylinder, aft-edge fillet, and ONE recessed nozzle study."""

from cadgen import build123d as bd

from concept_shapes import SEPARATION, STUDIES, tag
from spear_banded_cap_shapes import detailed_nozzle, radial, recessed_throat, cylinder
from spear_revision_shapes import make_selected_spear


CAP_AFT = -600.
CAP_FWD = -420.
CAP_RADIUS = STUDIES["A"]["radius"] * .98  # flush with main body at its aft datum
AFT_FILLET_RADIUS = 22.


def cylindrical_cap(radius=CAP_RADIUS, aft=CAP_AFT, forward=CAP_FWD,
                    socket_x=-470.):
    raw = (bd.Cylinder(radius, forward-aft,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
           .rotate(bd.Axis.Y, 90).translate((aft, 0, 0)))
    aft_rim = [edge for edge in raw.edges()
               if abs(edge.bounding_box().min.X-aft) < .0001
               and abs(edge.bounding_box().max.X-aft) < .0001]
    assert len(aft_rim) == 1, f"expected one aft circular edge, found {len(aft_rim)}"
    rounded = bd.fillet(aft_rim, AFT_FILLET_RADIUS)
    # Historical cap places one nozzle at X=-470. A later shortened cap must
    # pass socket_x=None and cut its new socket at its own nozzle station.
    if socket_x is not None:
        socket = radial(cylinder(6.4, 20.), 48., socket_x)
        rounded = rounded-socket
    return tag(rounded, "turning_cap", "#949EA3")


def make_cylindrical_cap_preview(separated=False, cap_only=False):
    base = make_selected_spear()
    parts = [cylindrical_cap() if item.label == "turning_cap" else
             detailed_nozzle() if item.label == "thruster_0" else item
             for item in base.children]
    parts.append(recessed_throat())
    if cap_only:
        parts = [item for item in parts
                 if item.label == "turning_cap" or item.label.startswith("thruster_")]
    elif separated:
        parts = [item.moved(bd.Location((-SEPARATION, 0, 0)))
                 if item.label == "turning_cap" or item.label.startswith("thruster_")
                 else item for item in parts]
    suffix = "_Cap_Focus" if cap_only else ("_Separated" if separated else "")
    return bd.Compound(children=parts, label=f"Spear_CylinderFillet_Nozzle0{suffix}")
