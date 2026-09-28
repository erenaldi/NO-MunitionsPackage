"""130 mm cylinder cap with flush extended body and slightly thinner SketchLow fins."""

from cadgen import build123d as bd

from concept_shapes import SEPARATION, STUDIES, cap_thruster, cylinder as cylinder_x, fin, profile, tag
from spear_banded_cap_shapes import cylinder, detailed_nozzle, radial, recessed_throat
from spear_cylinder_cap_shapes import cylindrical_cap
from spear_flush_junction_shapes import make_flush_junction
from spear_revision_shapes import FIN_VARIANTS


AFT = -600.
OLD_SEAM = -420.
NEW_SEAM = -470.
RADIUS = STUDIES["A"]["radius"]
NOZZLE_X = -535.
ROOT_THICKNESS = 6.
TIP_THICKNESS = 2.


def lengthened_body():
    """One loft: added 50 mm cylinder then the original A forward stations."""
    spec = STUDIES["A"]
    nose = spec["length"]/2
    base = nose-spec["nose"]
    stations = [(NEW_SEAM, 1.), (OLD_SEAM, 1.), (OLD_SEAM+22., 1.),
                (OLD_SEAM+165., .92), (base-165., .89), (base, .88),
                (base+spec["nose"]*.44, .61),
                (base+spec["nose"]*.78, .28), (nose, .024)]
    shell = bd.Solid.make_loft([profile(x, RADIUS*factor) for x, factor in stations],
                               ruled=True)
    # The body-owned recess extends continuously from the new aft face to the
    # original blind floor at X=-367. It is not sealed by a fused extension.
    cavity = cylinder_x(NEW_SEAM-1, OLD_SEAM+53, RADIUS*.61)
    return tag(shell-cavity, "body")


def short_cap():
    cap = cylindrical_cap(radius=RADIUS, aft=AFT, forward=NEW_SEAM, socket_x=None)
    socket = radial(cylinder(6.4, 20.), 48., NOZZLE_X)
    return tag(cap - socket, "turning_cap", "#949EA3")


def make_short_cap(separated=False, cap_only=False):
    source = make_flush_junction()
    spec = STUDIES["A"]
    selected_fin = FIN_VARIANTS["SketchLow"]
    station = dict(spec, cap=NEW_SEAM-AFT, nozzle_x=.5)
    parts = []
    for item in source.children:
        name = item.label
        if name == "body":
            parts.append(lengthened_body())
        elif name == "turning_cap":
            parts.append(short_cap())
        elif name == "main_nozzle":
            parts.append(tag(item.translate((NEW_SEAM-OLD_SEAM, 0, 0)),
                             "main_nozzle", "#30383B"))
        elif name == "thruster_0":
            parts.append(detailed_nozzle(NOZZLE_X))
        elif name == "thruster_0_throat":
            parts.append(recessed_throat(NOZZLE_X))
        elif name.startswith("thruster_"):
            parts.append(cap_thruster(station, int(name.split("_")[1])))
        elif name.startswith("aft_fin_"):
            index = int(name.split("_")[2])
            angle = spec["fin_clock"]+90*index
            parts.append(fin(spec, angle,
                             OLD_SEAM+selected_fin["root_aft"],
                             OLD_SEAM+selected_fin["root_fwd"],
                             OLD_SEAM+selected_fin["tip_aft"],
                             OLD_SEAM+selected_fin["tip_fwd"],
                             spec["fin_root"], selected_fin["tip_radius"], name,
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
    suffix = "_Cap_Focus" if cap_only else ("_Separated" if separated else "")
    return bd.Compound(children=parts, label=f"Spear_ShortCap_ThinFins{suffix}")
