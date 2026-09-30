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


def concept_4(nose, tail):
    """Inline sensor barrels: collar + cylinder + bezel + IR dome per tip.

    Built along +X at the front tip, mirrored for the rear. The collar cone
    starts inside the tapering shell and is clipped by it, so it emerges as a
    fairing around the tip; nothing is subtracted from the housing.
    """
    parts = []
    for name, shell, tip, cz, sign in (
            ("front", nose, FRONT_TIP, -135., 1),
            ("rear", tail, abs(AFT_TIP), -111.5, -1)):
        def along_x(shape, x_mid):
            return shape.translate((x_mid, 0, cz))
        cone = bd.Cone(34, 21, 53, rotation=(0, 90, 0))
        collar = along_x(cone, tip-45+53/2)
        barrel = along_x(bd.Cylinder(21, 67, rotation=(0, 90, 0)), tip+8+67/2)
        bezel = along_x(bd.Cylinder(24.5, 9, rotation=(0, 90, 0)), tip+75+4.5)
        dome = bd.Sphere(21) & bd.Box(60, 60, 60).translate((30, 0, 0))
        dome = dome.translate((tip+84, 0, cz))
        if sign < 0:
            shell_pos = shell.mirror(bd.Plane.YZ)
        else:
            shell_pos = shell
        body = (collar+barrel) - shell_pos
        body.label = f"sensor_{name}_barrel"
        pieces = [body, bezel, dome]
        bezel.label = f"sensor_{name}_bezel"
        dome.label = f"sensor_{name}_dome"
        for p in pieces:
            if sign < 0:
                lab = p.label
                p = p.mirror(bd.Plane.YZ)
                p.label = lab
            parts.append(p)
    return parts


def dome(radius, cz, x0, sign):
    """Half-sphere on the +/-X side of x0, flat face seated at x0."""
    ball = bd.Sphere(radius).translate((x0, 0, cz))
    half = bd.Box(radius+1, 2*radius+2, 2*radius+2).translate(
        (x0+sign*(radius+1)/2, 0, cz))
    return ball & half


# satellite layout read from the user's markup (front view, mm from the end
# axis: dy right/+Y, dz up), dome diameter, and how far the dome ends behind
# the central mast's dome (from the side-view guide lines)
SATELLITES = (("large", -80., 31., 70., 58.),
              ("medium", 130., 55., 44., 48.),
              ("small", 51., -29., 34., 43.))


def satellite(shell, name, end, sign, cy, cz, dome_d, behind, k, prior):
    """Inline neck + ring + dome seated on the shell surface at (cy, cz)."""
    y, z = cy*k, end["cz"]+cz*k
    probe = bd.Cylinder(.5, 900, rotation=(0, 90, 0)).translate(
        (end["tip"]+sign*(-450+200), y, z))
    hit = probe & shell
    assert hit is not None and hit.volume > 0, (name, "no surface at", y, z)
    box = hit.bounding_box()
    x_hit = box.max.X if sign > 0 else box.min.X
    x_end = end["mast_end"]-sign*behind*k
    r_dome = dome_d*k/2
    x_base = x_end-sign*r_dome
    assert (x_base-x_hit)*sign > 4, (name, "no room for a neck", x_hit, x_base)
    a, b = sorted((x_hit-sign*30, x_base))
    neck = bd.Cylinder(r_dome*.8, b-a, rotation=(0, 90, 0)).translate(
        ((a+b)/2, y, z)) - shell
    ring_c = (x_hit+x_base)/2
    ring = bd.Cylinder(r_dome*.98, 8, rotation=(0, 90, 0)).translate(
        (ring_c, y, z))
    cap = dome(r_dome, z, x_base, sign).translate((0, y, 0))
    parts = []
    for part, label in ((neck, "neck"), (ring, "ring"), (cap, "dome")):
        for other in prior+parts:
            part = part - other
        part = part - shell
        assert part.volume > 5, (name, label, "empty/sliver after subtraction")
        part.label = f"sensor_{end['name']}_{name}_{label}"
        parts.append(part)
    return parts


def concept_5(nose, tail):
    """C4 mast plus three staggered inline satellites (user markup intent)."""
    base = concept_4(nose, tail)
    parts = list(base)
    for end_name, shell, tip, sign, k, mast in (
            ("front", nose, FRONT_TIP, 1, 1., 105.),
            ("rear", tail, AFT_TIP, -1, .8, 105.)):
        end = {"name": end_name, "tip": tip, "mast_end": tip+sign*mast,
               "cz": -135. if sign > 0 else -111.5}
        prior = [p for p in parts if p.label.startswith(f"sensor_{end_name}")]
        for name, cy, cz, dome_d, behind in SATELLITES:
            sat = satellite(shell, name, end, sign, cy*(1 if sign > 0 else -1),
                            cz, dome_d, behind, k, prior)
            prior += sat
            parts += sat
    return parts


def concept_6(nose, tail):
    """Three staggered inline satellites per end; no central mast."""
    parts = []
    for end_name, shell, tip, sign, k in (("front", nose, FRONT_TIP, 1, 1.),
                                          ("rear", tail, AFT_TIP, -1, .8)):
        end = {"name": end_name, "tip": tip, "mast_end": tip+sign*105.,
               "cz": -135. if sign > 0 else -111.5}
        for name, cy, cz, dome_d, behind in SATELLITES:
            parts += satellite(shell, name, end, sign,
                               cy*(1 if sign > 0 else -1), cz, dome_d, behind,
                               k, parts)
    return parts


CONCEPTS = {1: concept_1, 2: concept_2, 3: concept_3, 4: concept_4,
            5: concept_5, 6: concept_6}


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
