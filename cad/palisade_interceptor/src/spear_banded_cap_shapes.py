"""Reference-led straight-band turning cap with ONE detailed lateral nozzle."""

from cadgen import build123d as bd

from concept_shapes import SEPARATION, STUDIES, profile, tag
from spear_revision_shapes import make_selected_spear


NOZZLE_X = -470.
REAR = -600.
DOME_RADIUS = 34.
BAND_AFT = -520.
SEAM = -420.


def radial(part, radial_start, x=NOZZLE_X):
    """Turn local +Z into cap +Y (the prototyped 0-degree nozzle station)."""
    return part.rotate(bd.Axis.X, -90.).translate((x, radial_start, 0.))


def cylinder(radius, height):
    return bd.Cylinder(radius, height,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def banded_cap():
    """~100 mm straight band, ~46 mm cone, then 34 mm round closed end."""
    r = STUDIES["A"]["radius"]
    dome = bd.Sphere(DOME_RADIUS).translate((REAR+DOME_RADIUS, 0, 0))
    dome &= bd.Box(DOME_RADIUS+.5, 80., 80.).translate(
        (REAR+(DOME_RADIUS+.5)/2, 0, 0))
    fore = bd.Solid.make_loft([
        profile(REAR+DOME_RADIUS, DOME_RADIUS),
        profile(BAND_AFT, r),
        profile(SEAM-10., r),
        profile(SEAM, r*.98),
    ], ruled=True)
    cap = dome.fuse(fore)
    # A blind radial socket behind only the first lateral thruster. The other
    # three remain original while the user judges the proposed nozzle detail.
    blind_socket = radial(cylinder(6.4, 20.), 48.)
    return tag(cap - blind_socket, "turning_cap", "#949EA3")


def detailed_nozzle(x=NOZZLE_X):
    """Compact raised stepped lip, flared bore and actual recessed throat."""
    seat = cylinder(12., 4.)
    flare = bd.Cone(12., 9.5, 4.5,
                    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    flare = flare.translate((0, 0, 3.))
    lip = cylinder(10.2, 1.3).translate((0, 0, 6.9))
    exterior = seat.fuse(flare, lip)
    bore = bd.Cone(5.5, 7.6, 9.,
                   align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    bore = bore.translate((0, 0, -.2))
    front_counterbore = cylinder(8.1, 2.3).translate((0, 0, 6.6))
    nozzle = exterior - bore - front_counterbore
    return tag(radial(nozzle, 60., x), "thruster_0", "#30383B")


def recessed_throat(x=NOZZLE_X):
    """Dark blind back at the bottom of the cap's actual radial socket."""
    return tag(radial(cylinder(5.8, 2.), 48., x), "thruster_0_throat", "#11171B")


def make_banded_cap_preview(separated=False, cap_only=False):
    source = make_selected_spear()
    parts = [banded_cap() if item.label == "turning_cap" else
             detailed_nozzle() if item.label == "thruster_0" else item
             for item in source.children]
    parts.append(recessed_throat())
    if cap_only:
        parts = [item for item in parts
                 if item.label == "turning_cap" or item.label.startswith("thruster_")]
    elif separated:
        parts = [item.moved(bd.Location((-SEPARATION, 0, 0)))
                 if item.label == "turning_cap" or item.label.startswith("thruster_")
                 else item for item in parts]
    state = "_Cap_Focus" if cap_only else ("_Separated" if separated else "")
    return bd.Compound(children=parts, label=f"Spear_BandedCap_Nozzle0{state}")
