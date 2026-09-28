"""Exterior game-art studies. mm, +X nose, +Z dorsal; no functional internals.

The screenshot's broad corner radius is inferred as 70 mm at 200 mm width.
Separation is a rigid review offset, not a simulated staging mechanism.
"""
import math
from cadgen import build123d as bd, srgb

LENGTH = 3370.0
HALF = LENGTH / 2
SEAM = -LENGTH / 3
WIDTH = 200.0
CORNER = 70.0
TRANSITION_START = 740.0
NOSE_BASE = 1085.0
NOSE_RADIUS = 95.0
SEPARATION = 340.0
ANGLES = (0, 90, 180, 270)

# Coherent differences: restrained side rails / blended corner chines /
# wider flat-face shoulders with cropped control fins. All remain low-profile.
STUDIES = {
    "A": dict(name="Trace", mouth=630., aft=-805., width=42., height=17.,
              clock=0., finclock=45., main=(-1100., -805., -1105., -995., 185.),
              boost=(-1655., -1360., -1668., -1540., 194.)),
    "B": dict(name="Chine", mouth=725., aft=-930., width=32., height=15.,
              clock=45., finclock=0., main=(-1108., -735., -1100., -970., 171.),
              boost=(-1660., -1335., -1670., -1530., 185.)),
    "C": dict(name="Shoulder", mouth=495., aft=-675., width=62., height=19.,
              clock=0., finclock=45., main=(-1100., -870., -1090., -930., 202.),
              boost=(-1645., -1430., -1660., -1490., 206.)),
}


def tag(shape, label, shade="#B5BDC3"):
    shape.label = label
    shape.color = srgb(shade)
    return shape


def section(x, width=WIDTH, corner=CORNER):
    return bd.RectangleRounded(width, width, corner).rotate(bd.Axis.Y, 90).translate((x, 0, 0))


def disk(x, radius):
    return bd.Circle(radius).rotate(bd.Axis.Y, 90).translate((x, 0, 0))


def barrel(a, b, radius):
    return bd.loft([disk(a, radius), disk(b, radius)], ruled=True)


def rotate(shape, angle):
    return shape.rotate(bd.Axis.X, -angle)


def ogive():
    length = HALF - NOSE_BASE
    rho = (length * length + NOSE_RADIUS * NOSE_RADIUS) / (2 * NOSE_RADIUS)
    # A spline loft approximates the tangent ogive, avoiding a spindle-torus
    # singularity rejected by the independent STEP reader. 0.35 mm tip radius.
    profiles = []
    for i in range(17):
        x = length * i / 16
        radius = max(0.35, math.sqrt(rho*rho-x*x) + NOSE_RADIUS-rho)
        profiles.append(disk(NOSE_BASE+x, radius))
    return bd.loft(profiles, ruled=False)


def body():
    straight = bd.extrude(section(SEAM), amount=TRANSITION_START-SEAM, dir=(1, 0, 0))
    # Compatible rounded profiles fade the flats out with zero end slope.
    profiles = []
    for i in range(9):
        t = i / 8
        ease = t*t*(3-2*t)
        w = WIDTH + (2*NOSE_RADIUS-WIDTH)*ease
        r = CORNER + (NOSE_RADIUS-0.01-CORNER)*ease
        profiles.append(section(TRANSITION_START + (NOSE_BASE-1-TRANSITION_START)*t, w, r))
    transition = bd.loft(profiles, ruled=False)
    tipblend = bd.loft([profiles[-1], disk(NOSE_BASE, NOSE_RADIUS)], ruled=True)
    result = straight + transition + tipblend
    # A shallow visual exhaust recess exposed only in the separated state.
    recess = bd.loft([disk(SEAM-1, 65), disk(SEAM+36, 37), disk(SEAM+42, 37)], ruled=True)
    return result - recess


def booster():
    rear = bd.loft([disk(-HALF, 82), section(-HALF+100, 190, 79),
                    section(-HALF+165)], ruled=False)
    straight = bd.extrude(section(-HALF+165), amount=SEAM-(-HALF+165), dir=(1, 0, 0))
    result = rear + straight
    cavity = bd.loft([disk(-HALF-1, 69), disk(-HALF+64, 33), disk(-HALF+72, 33)], ruled=True)
    return result - cavity


def fin(spec, root, angle, label):
    aft, forward, tipaft, tipforward, radius = spec
    wires = []
    for z, a, b, thickness in ((root, aft, forward, 8.), (radius, tipaft, tipforward, 2.8)):
        wires.append(bd.Wire.make_polygon([
            (a, 0, z), (a+(b-a)*0.45, -thickness/2, z),
            (b, 0, z), (a+(b-a)*0.45, thickness/2, z),
        ], close=True))
    return tag(rotate(bd.Solid.make_loft(wires, ruled=True), angle), label, "#929DA5")


def intake(key):
    p = STUDIES[key]
    # At 45 degrees the broad rounded corner has radius 112.426... mm.
    base = 100. if p["clock"] == 0 else math.sqrt(2)*30 + CORNER
    aft, mouth, width, height = (p[n] for n in ("aft", "mouth", "width", "height"))

    def trapezoid(x, w, h):
        return bd.Face(bd.Wire.make_polygon([
            (x, -w/2, base-3), (x, w/2, base-3),
            (x, w*0.36, base+h), (x, -w*0.36, base+h),
        ], close=True))

    outer = bd.loft([trapezoid(aft, width*.28, 1.),
                     trapezoid(aft+180, width*.82, height*.60),
                     trapezoid(mouth-210, width, height),
                     trapezoid(mouth, width, height)], ruled=True)
    # Open forward mouth and deep blind passage. Neutral shading reveals real relief.
    def opening(x, w, bottom, top):
        return bd.Face(bd.Wire.make_polygon([(x,-w/2,bottom), (x,w/2,bottom),
                                           (x,w/2,top), (x,-w/2,top)], close=True))
    cutter = bd.loft([opening(mouth+2, width*.62, base+2, base+height-3),
                      opening(mouth-180, width*.46, base+2, base+height-5)], ruled=True)
    return outer - cutter


def build_study(key, separated=False):
    p = STUDIES[key]
    parts = [tag(body(), "main_body"), tag(ogive(), "main_ogive", "#C3C9CE")]
    duct = intake(key)
    for i, angle in enumerate(ANGLES, 1):
        parts.append(tag(rotate(duct, angle+p["clock"]), f"main_intake_{i}"))
        root = 98. if p["finclock"] == 0 else 110.
        parts.append(fin(p["main"], root, angle+p["finclock"], f"main_fin_{i}"))
    boost = [tag(booster(), "booster_body", "#A7B0B7")]
    for i, angle in enumerate(ANGLES, 1):
        root = 97. if p["finclock"] == 0 else 108.
        boost.append(fin(p["boost"], root, angle+p["finclock"], f"booster_fin_{i}"))
    for part in boost:
        parts.append(part.moved(bd.Location((-SEPARATION, 0, 0))) if separated else part)
    return bd.Compound(children=parts, label=f"Halberd_{key}_{p['name']}" + ("_Separated" if separated else ""))
