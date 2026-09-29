"""A12 additive sensor studies on the approved A11 nose and A10 rear cap.

The approved shells are untouched: every sensor is a separate solid built as
(footprint prism ∩ shell offset outward by T) − shell, so it only adds skin on
top of the existing surface. Nothing is placed on the roof (the pod hangs
under the airframe) or below the flat belly at Z -223. Study geometry only.
"""

import math

from cadgen import build123d as bd

from continuous_ends import section
from drooped_ends import AFT_ROOT, AFT_TIP, VALUES, level_fairing
from housing import cassettes, housing, solid_box
from teal_nose import (FRONT_ROOT, FRONT_TIP, STATIONS, TIP_BELLY, TIP_TOP,
                       profile, teal_fairing)


def nose_offset(T):
    wires = []
    for t in STATIONS:
        x = FRONT_ROOT+(FRONT_TIP-FRONT_ROOT)*t
        scale = 1. if t <= .02 else math.sqrt(max(0., 1-t*t))
        if t == 1.:
            w, h, r, cz = 24., 12., 5.4, -135.
        else:
            roof, belly = profile(t)
            w, h = 399.9*scale, roof-belly
            cz = (roof+belly)/2 if t else -111.5
            h = h if t else 223.
            r = 12+(.45*h-12)*(t**1.5)
        wires.append(section(x, w+2*T, h+2*T, r+T, cz))
    return bd.Solid.make_loft(wires, ruled=False)


def tail_offset(T):
    wires = []
    for t in reversed(VALUES):
        x = AFT_ROOT+(AFT_TIP-AFT_ROOT)*t
        scale = 1. if t <= .02 else math.sqrt(max(0., 1-t*t))
        if t == 1.:
            w, h, r = 8., 4., 1.7
        else:
            w = 399.9*scale
            h = 223. if t == 0. else 222.9*scale
            r = 12+(.45*h-12)*(t**1.5)
        wires.append(section(x, w+2*T, h+2*T, r+T, -111.5))
    return bd.Solid.make_loft(wires, ruled=False)


def stadium_y(cx, cz, length, height, y0, y1):
    """Rounded-slot prism in XZ, extruded along Y from y0 to y1."""
    r = height/2
    core = bd.Box(max(length-height, 1e-3), y1-y0, height)
    caps = [bd.Cylinder(r, y1-y0, rotation=(90, 0, 0)).translate(
        (dx*(length-height)/2, 0, 0)) for dx in (-1, 1)]
    body = core+caps[0]+caps[1]
    return body.translate((cx, (y0+y1)/2, cz))


def skin(prism, offset_loft, shell, label):
    part = (prism & offset_loft) - shell
    part.label = label
    return part


def shells():
    return teal_fairing(FRONT_ROOT, FRONT_TIP, "n"), level_fairing(
        AFT_ROOT, AFT_TIP, "t")


def stadium_x(cy, cz, span_y, height, x0, x1):
    """Rounded-slot prism in YZ, extruded along X from x0 to x1."""
    r = height/2
    core = bd.Box(x1-x0, max(span_y-height, 1e-3), height)
    caps = [bd.Cylinder(r, x1-x0, rotation=(0, 90, 0)).translate(
        (0, dy*(span_y-height)/2, 0)) for dy in (-1, 1)]
    return (core+caps[0]+caps[1]).translate(((x0+x1)/2, cy, cz))


def mirrored(prism, sign):
    return prism.mirror(bd.Plane.XZ) if sign < 0 else prism


def concept_1(nose, tail):
    """Two-step tip caps (4 + 8 mm skin) with a forward lens button each end."""
    parts = []
    for name, shell, off4, off8, x0, x1, sign, tip, span, ht in (
            ("front", nose, nose_offset(4.), nose_offset(8.), 1560., 1640.,
             1, FRONT_TIP, 30., 16.),
            ("rear", tail, tail_offset(4.), tail_offset(8.), -1490., -1550.,
             -1, AFT_TIP, 18., 9.)):
        big = bd.Box(600, 500, 500).translate((x1+sign*300, 0, -111.5))
        small = bd.Box(600, 500, 500).translate((x0+sign*300, 0, -111.5))
        step4 = skin(small, off4, shell, f"sensor_{name}_cap_step")
        cap8 = skin(big, off8, shell, f"sensor_{name}_cap")
        # cap8 sits over step4's footprint; keep it a true second tier
        cap8 = cap8 - off4
        cap8.label = f"sensor_{name}_cap"
        cz = -135. if name == "front" else -111.5
        lo, hi = (tip, tip+3.) if sign > 0 else (tip-3., tip)
        lens = stadium_x(0, cz, span, ht, lo, hi)
        lens.label = f"sensor_{name}_lens"
        parts += [step4, cap8, lens]
    return parts


def concept_2(nose, tail):
    """Cheek pads (6 mm) each side with a 1.5 mm proud lens window."""
    parts = []
    for name, shell, cx, cz, ln, ht in (
            ("front", nose, 1585., -122., 200., 62.),
            ("rear", tail, -1510., -111.5, 110., 62.)):
        base = 6.
        off = (nose_offset if name == "front" else tail_offset)
        offp, offl = off(base), off(base+1.5)
        for sign, side in ((-1, "port"), (1, "starboard")):
            pad = skin(mirrored(stadium_y(cx, cz, ln, ht, 60, 260), sign),
                       offp, shell, f"sensor_{name}_{side}_pad")
            win = (mirrored(stadium_y(cx, cz, ln-26, ht-26, 60, 270), sign)
                   & offl) - offp
            win.label = f"sensor_{name}_{side}_lens"
            parts += [pad, win]
    return parts


def concept_3(nose, tail):
    """Chine bars: long 7 mm raised bar per side with a slim lens strip."""
    parts = []
    for name, shell, cx, cz, ln, ht in (
            ("front", nose, 1600., -165., 280., 30.),
            ("rear", tail, -1500., -165., 160., 30.)):
        off = (nose_offset if name == "front" else tail_offset)
        offb, offl = off(7.), off(8.5)
        for sign, side in ((-1, "port"), (1, "starboard")):
            bar = skin(mirrored(stadium_y(cx, cz, ln, ht, 40, 260), sign),
                       offb, shell, f"sensor_{name}_{side}_bar")
            win = (mirrored(stadium_y(cx, cz, ln-40, ht-18, 40, 270), sign)
                   & offl) - offb
            win.label = f"sensor_{name}_{side}_lens"
            parts += [bar, win]
    return parts


CONCEPTS = {1: concept_1, 2: concept_2, 3: concept_3}


def study(concept):
    from teal_nose import study as base
    nose, tail = shells()
    return bd.Compound(children=list(base(False).children)
                       + CONCEPTS[concept](nose, tail))


def crop(concept, end):
    """Review-only crop: one end's shell plus its sensors, and a beam stub."""
    nose, tail = shells()
    shell, sign = (nose, 1) if end == "front" else (tail, -1)
    shell.label = "shell"
    sensors = [p for p in CONCEPTS[concept](nose, tail)
               if p.label.startswith(f"sensor_{end}")]
    stub = solid_box("beam_stub", 120, 400, 223, (sign*1265, 0, -111.5))
    return bd.Compound(children=[shell, stub]+sensors)
