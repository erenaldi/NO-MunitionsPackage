"""A13 integrated sensor mounts (direction A: hooded / recessed / mixed types).

Built in a local frame (+X outward along the end axis, origin on the shell
surface at the mount axis), mirrored for the rear, then sunk into the shell and
clipped by it so everything is additive. Cosmetic study geometry only; the
vocabulary comes from SENSOR_REFERENCE_SURVEY.md.
"""

import math

from cadgen import build123d as bd

from continuous_ends import section
from sensors import SATELLITES, shells
from teal_nose import FRONT_TIP
from drooped_ends import AFT_TIP

BURY = -38.


def cyl(r, x0, x1):
    return bd.Cylinder(r, x1-x0, rotation=(0, 90, 0)).translate(
        ((x0+x1)/2, 0, 0))


def ring(r_out, r_in, x0, x1):
    return cyl(r_out, x0, x1)-cyl(r_in, x0-1, x1+1)


def ball(r, xc):
    """Front half of a sphere centred on the axis at xc."""
    return bd.Sphere(r).translate((xc, 0, 0)) & bd.Box(r+1, 2*r+2, 2*r+2).translate(
        (xc+(r+1)/2, 0, 0))


def bolts(r_circle, x, n=12, r=1.7, h=2.6):
    out = None
    for i in range(n):
        a = 2*math.pi*i/n
        b = cyl(r, x, x+h).translate((0, r_circle*math.cos(a), r_circle*math.sin(a)))
        out = b if out is None else out+b
    return out


def flange(rf, x0, t=5., n=12):
    """Disc flange with a bolt circle on its front face."""
    return cyl(rf, x0, x0+t) + bolts(rf-4.5, x0+t, n)


def halfspace(d, angle):
    """Big box beyond a plane tilted `angle` deg about Y, `d` mm along its normal."""
    box = bd.Box(600, 600, 600).translate((300+d, 0, 0))
    return box.rotate(bd.Axis.Y, angle)


def facet_window(r, x0, x_face, angle=32., proud=2.5, win=.86):
    """Barrel cut obliquely at the nose with a proud flat window plate."""
    p = (x_face, 0, 0)
    body = cyl(r, x0, x_face+r*1.2) - halfspace(0, angle).translate(p)
    plate = (cyl(r*win, x_face-r, x_face+r*1.5) & halfspace(0, angle).translate(p)) \
        - halfspace(proud, angle).translate(p)
    return body, plate


def visor(r, x0, x1, thick=3.6):
    """Half-shell hood over the upper side of a lens."""
    return ring(r, r-thick, x0, x1) & bd.Box(x1-x0+2, 2*r+2, r+1).translate(
        ((x0+x1)/2, 0, (r+1)/2-.12*r))


def bullet(r, x0, x1, tmax=1.):
    wires = []
    base = (0., .15, .35, .55, .72, .85, .94, .985, 1.)
    for t in [v*tmax for v in base]:
        x = x0+(x1-x0)*t
        rad = max(r*math.sqrt(max(0., 1-t**2.4)), .6)
        pts = [(x, rad*math.cos(2*math.pi*i/36), rad*math.sin(2*math.pi*i/36))
               for i in range(36)]
        wires.append(bd.Wire.make_polygon(pts, close=True))
    return bd.Solid.make_loft(wires, ruled=False)


# ---- the three vocabularies -------------------------------------------------

def d1(kind, r):
    if kind == "large":            # hooded ball lens
        return {"plinth": cyl(r, BURY, 12), "seam": cyl(r+1.4, 11, 14),
                "hood": visor(r+4, 6, 46), "lens": ball(r*.84, 14),
                "bolts": bolts(r-4.5, 14., 16)}
    if kind == "medium":           # faceted window in a short barrel
        body, plate = facet_window(r, BURY, 34., 30.)
        return {"barrel": body, "window": plate, "flange": flange(r+6, 4.)}
    bez = ring(r, r-3.6, BURY, 20)  # small: dome in bezel
    return {"bezel": bez, "base": cyl(r-3.6, BURY, 6), "dome": ball(r*.68, 8),
            "flange": flange(r+6, 3.), "seat": ring(r+1.6, r-.4, 15, 19)}


def d2(kind, r):
    if kind == "large":            # stepped turret, ball head, seam, flange
        return {"base": cyl(r, BURY, 32), "band": ring(r+1.6, r-1, 16, 19),
                "flange": flange(r+7, 0.), "step": cyl(r*.84, 32, 60),
                "seam": cyl(r*.84+1.8, 59, 62), "head": ball(r*.84, 60)}
    if kind == "medium":           # sniper-style barrel with panel bands
        body, plate = facet_window(r, BURY, 70., 35.)
        return {"barrel": body, "window": plate,
                "band1": ring(r+1.4, r-1, 18, 21), "band2": ring(r+1.4, r-1, 44, 47),
                "flange": flange(r+6, 2.)}
    return {"neck": cyl(r*.8, BURY, 56), "bezel": ring(r+2, r*.8-.4, 46, 60),
            "dome": ball(r*.78, 54), "flange": flange(r+7, 6.),
            "band": ring(r*.8+1.4, r*.8-1, 24, 27)}


def d3(kind, r):
    if kind == "large":            # faired blister, faceted window
        b = bullet(r, BURY, 62)
        cut = halfspace(0, 34.).translate((46, 0, 0))
        body = b - cut
        plate = (bullet(r*.86, BURY, 62) & cut) - halfspace(2.4, 34.).translate((46, 0, 0))
        return {"blister": body, "window": plate}
    r_face = None
    if kind == "medium":           # blister with round lens on a bezelled face
        x1 = 52.
    else:
        x1 = 42.
    b = bullet(r, BURY, x1, .9)
    xf = BURY+(x1-BURY)*.9
    rf = r*math.sqrt(1-.9**2.4)
    return {"blister": b, "bezel": ring(rf+1.8, rf-1.5, xf-4, xf+1.5),
            "lens": ball(rf*.9, xf-1)}


def d4(kind, r):
    """A+B blend: D2 protruding hardware with D1-style hoods over the lenses."""
    parts = dict(d2(kind, r))
    if kind == "large":            # ball head under a half-shell visor
        parts["hood"] = visor(r*.84+4.5, 46, 76, thick=4.5)
    elif kind == "medium":         # faceted window under a scoop hood
        parts["hood"] = visor(r+3.4, 46, 80, thick=3.4)
    else:                          # small: brow visor over the bezel
        parts["hood"] = visor(r+5.6, 48, 68, thick=3.6)
    return parts


VOCAB = {"D1": d1, "D2": d2, "D3": d3, "D4": d4}


def surface_x(shell, sign, tip, y, z):
    probe = bd.Cylinder(.5, 900, rotation=(0, 90, 0)).translate((tip-sign*250, y, z))
    hit = probe & shell
    assert hit is not None and hit.volume > 0, ("no surface at", y, z)
    b = hit.bounding_box()
    return b.max.X if sign > 0 else b.min.X


def build(concept, ends=("front", "rear")):
    nose, tail = shells()
    parts = []
    for end, shell, tip, sign, k in (("front", nose, FRONT_TIP, 1, 1.),
                                     ("rear", tail, AFT_TIP, -1, .8)):
        if end not in ends:
            continue
        cz0 = -135. if sign > 0 else -111.5
        placed = []
        for kind, cy, cz, dome_d, _ in SATELLITES:
            y, z = cy*(1 if sign > 0 else -1)*k, cz0+cz*k
            x0 = surface_x(shell, sign, tip, y, z)
            for label, shape in VOCAB[concept](kind, dome_d/2).items():
                s = shape.scale(k) if k != 1. else shape
                if sign < 0:
                    s = s.mirror(bd.Plane.YZ)
                s = s.translate((x0, y, z)) - shell
                for other in placed:
                    s = s - other
                placed.append(s)
                pieces = [p for p in s.solids() if p.volume > 3]
                if not pieces:      # buried in the shell: nothing to add
                    print("skipped buried part:", concept, end, kind, label)
                    continue
                for i, piece in enumerate(pieces):
                    suffix = f"_{i+1}" if len(pieces) > 1 else ""
                    piece.label = f"sensor_{end}_{kind}_{label}{suffix}"
                    parts.append(piece)
    return parts


def study(concept):
    from teal_nose import study as base
    return bd.Compound(children=list(base(False).children)+build(concept))


def crop(concept, end):
    from housing import solid_box
    nose, tail = shells()
    shell, sign = (nose, 1) if end == "front" else (tail, -1)
    shell.label = "shell"
    sensors = [p for p in build(concept) if p.label.startswith(f"sensor_{end}")]
    stub = solid_box("beam_stub", 120, 400, 223, (sign*1265, 0, -111.5))
    return bd.Compound(children=[shell, stub]+sensors)
