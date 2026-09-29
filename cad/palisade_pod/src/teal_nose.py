"""A11 silhouette: A10 frame with a nose traced from the user's teal outline.

User direction (2026-09-28): a side-view reference drawing whose teal outline
(not the sky-blue body or the red line) defines the forward fairing. The
outline was extracted by colour from the image and scaled with the known
beam height (223 mm) and A10 nose length: 2.027 px/mm, 487 mm long, tip at
mid-height (Z about -135) instead of on the belly line. The stroke is hand-drawn and
inaccurate, so `profile()` is a smooth fit of its intent. The rear
cap and everything else stay as approved A10. Dimensions are millimetres.
"""

import math

from cadgen import build123d as bd

from continuous_ends import section
from drooped_ends import AFT_ROOT, AFT_TIP, level_fairing
from housing import cassettes, housing, solid_box

FRONT_ROOT, FRONT_TIP = 1325., 1812.
TIP_CENTRE_Z = -135.
# denser than A10 near the tip, where the belly rises steeply
STATIONS = (0., .02, .08, .16, .28, .4, .52, .64, .72, .8, .86, .91, .94,
            .96, .975, .985, .992, .997, 1.)
TIP_TOP, TIP_BELLY = -129., -141.     # 12 mm blunt tip centred at -135


def _superellipse(t, n, m):
    """0 at t=0 with a level tangent, 1 at t=1 with a vertical tangent."""
    return 1-(1-t**n)**(1/m)


def profile(t):
    """(top Z, belly Z) as two independent curves - deliberately asymmetric.

    Least-squares fits to the hand-drawn teal outline: the roof leaves the
    beam top early and sweeps down (n=1.75, m=1.4, within ~4 mm); the belly
    stays near the -223 underside for most of the length and rises only
    toward the tip (n=1.88, m=2.59, within ~5 mm away from the tip cap).
    The drawing is a gesture, so this is an interpretation of intent.
    """
    return (TIP_TOP*_superellipse(t, 1.75, 1.4),
            -223.+(223.+TIP_BELLY)*_superellipse(t, 1.88, 2.59))


def teal_fairing(root, tip, label):
    wires = []
    for t in STATIONS:
        x = root+(tip-root)*t
        scale = math.sqrt(max(0., 1-t*t))
        if t <= .02:
            scale = 1.
        if t == 1.:
            width, height, radius, centre_z = 24., 12., 5.4, TIP_CENTRE_Z
        else:
            roof, belly = profile(t)
            width = 399.9*scale
            height = roof-belly if t else 223.
            centre_z = (roof+belly)/2 if t else -111.5
            radius = 12+(.45*height-12)*(t**1.5)
        wires.append(section(x, width, height, radius, centre_z))
    shape = bd.Solid.make_loft(wires, ruled=False)
    shape.label = label
    return shape


def study(filled):
    frame = [part for part in housing() if part.label not in (
        "forward_sensor_shell", "aft_sensor_shell", "forward_aperture",
        "aft_aperture", "port_outer_rail", "starboard_outer_rail")]
    frame.extend((teal_fairing(FRONT_ROOT, FRONT_TIP, "forward_sensor_shell"),
                  level_fairing(AFT_ROOT, AFT_TIP, "aft_sensor_shell")))
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
