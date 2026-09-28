"""One-diameter Spear barrel and matching shortened turning cap study."""

from cadgen import build123d as bd

from concept_shapes import SEPARATION, STUDIES, cap_thruster, cylinder as cylinder_x, fin, profile, tag
from spear_banded_cap_shapes import cylinder, radial
from spear_cylinder_cap_shapes import cylindrical_cap
from spear_revision_shapes import FIN_VARIANTS
from spear_short_cap_shapes import AFT, NEW_SEAM, NOZZLE_X, ROOT_THICKNESS, TIP_THICKNESS, make_short_cap


ORIGINAL_RADIUS = STUDIES["A"]["radius"]
BARREL_RADIUS = ORIGINAL_RADIUS * .88  # existing A/Spear nose-base radius: 54.56 mm
FIN_ROOT_RADIUS = 52.5
CAP_DETAIL_RADIAL_SHIFT = (BARREL_RADIUS-2.)-60.  # -7.44 mm, 0-degree +Y


def uniform_body():
    spec = STUDIES["A"]
    nose = spec["length"]/2
    nose_base = nose-spec["nose"]
    stations = [(NEW_SEAM, BARREL_RADIUS), (nose_base, BARREL_RADIUS),
                (nose_base+spec["nose"]*.44, ORIGINAL_RADIUS*.61),
                (nose_base+spec["nose"]*.78, ORIGINAL_RADIUS*.28),
                (nose, ORIGINAL_RADIUS*.024)]
    shell = bd.Solid.make_loft([profile(x, r) for x, r in stations], ruled=True)
    # Keep the original motor-cavity bore and its X=-367 blind floor.
    cavity = cylinder_x(NEW_SEAM-1., -367., ORIGINAL_RADIUS*.61)
    return tag(shell-cavity, "body")


def small_cap():
    cap = cylindrical_cap(radius=BARREL_RADIUS, aft=AFT, forward=NEW_SEAM,
                          socket_x=None)
    socket = radial(cylinder(6.4, 20.), BARREL_RADIUS-14., NOZZLE_X)
    return tag(cap-socket, "turning_cap", "#949EA3")


def make_uniform_spear(separated=False, cap_only=False):
    previous = make_short_cap()
    spec = STUDIES["A"]
    chosen = FIN_VARIANTS["SketchLow"]
    station = dict(spec, radius=BARREL_RADIUS, cap=NEW_SEAM-AFT, nozzle_x=.5)
    parts = []
    for item in previous.children:
        label = item.label
        if label == "body":
            parts.append(uniform_body())
        elif label == "turning_cap":
            parts.append(small_cap())
        elif label == "thruster_0":
            parts.append(tag(item.translate((0, CAP_DETAIL_RADIAL_SHIFT, 0)),
                             label, "#30383B"))
        elif label == "thruster_0_throat":
            parts.append(tag(item.translate((0, CAP_DETAIL_RADIAL_SHIFT, 0)),
                             label, "#11171B"))
        elif label.startswith("thruster_"):
            parts.append(cap_thruster(station, int(label.split("_")[1])))
        elif label.startswith("aft_fin_"):
            index = int(label.split("_")[2])
            angle = spec["fin_clock"]+index*90
            parts.append(fin(spec, angle,
                             -420.+chosen["root_aft"], -420.+chosen["root_fwd"],
                             -420.+chosen["tip_aft"], -420.+chosen["tip_fwd"],
                             FIN_ROOT_RADIUS, chosen["tip_radius"], label,
                             root_thickness=ROOT_THICKNESS,
                             tip_thickness=TIP_THICKNESS))
        else:
            parts.append(item)
    if cap_only:
        parts = [item for item in parts
                 if item.label == "turning_cap" or item.label.startswith("thruster_")]
    elif separated:
        parts = [item.moved(bd.Location((-SEPARATION, 0, 0)))
                 if item.label == "turning_cap" or item.label.startswith("thruster_")
                 else item for item in parts]
    state = "_Cap_Focus" if cap_only else ("_Separated" if separated else "")
    return bd.Compound(children=parts, label=f"Spear_UniformBarrel{state}")
