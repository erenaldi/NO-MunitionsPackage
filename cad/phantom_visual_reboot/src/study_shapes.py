"""RDM-9 paired silhouette studies; millimetres, +X forward, +Z dorsal.

Concept-stage exterior only. TALD supplies the flat wedge; Kh-69 supplies
faceted body/corner-folding tail; GBU-39 supplies long visible folded wings.
The dimensions below are inferred study choices, not reference measurements.
"""

import math

from cadgen import build123d as bd, srgb


LENGTH = 2800.0
STOW_RADIUS = 125.0

# Broadest section, forward shoulder, nose-flat width, main-wing station,
# wing semi-span, tail station, and tail exposure. Independent silhouettes,
# identical locked overall length and stowed envelope.
STUDIES = {
    "A": dict(name="Facet", width=202., height=108., shoulder=920.,
              nose=112., wing_x=-120., wing_span=505., wing_root=70.,
              tail_x=-1110., tail_span=79.),
    "B": dict(name="Shoulder", width=230., height=80., shoulder=1080.,
              nose=160., wing_x=-40., wing_span=555., wing_root=90.,
              tail_x=-1135., tail_span=72.),
    "C": dict(name="Keel", width=188., height=121., shoulder=1030.,
              nose=94., wing_x=-220., wing_span=470., wing_root=52., waist=152.,
              tail_x=-1090., tail_span=82.),
}


def tag(shape, name, color="#AAB5BA"):
    shape.label = name
    shape.color = srgb(color)
    return shape


def polygon(points):
    return bd.Face(bd.Wire.make_polygon(points, close=True))


def section(x, width, height, chamfer):
    y, z = width / 2, height / 2
    return polygon([(x, -y + chamfer, -z), (x, y - chamfer, -z),
                    (x, y, -z + chamfer), (x, y, z - chamfer),
                    (x, y - chamfer, z), (x, -y + chamfer, z),
                    (x, -y, z - chamfer), (x, -y, -z + chamfer)])


def body(spec):
    w, h = spec["width"], spec["height"]
    # Faceted 8-sided sections: the broad forward taper ends in a horizontal
    # flat rather than R5's point. Flat nose retains substantial top-view width.
    middle = spec.get("waist", w)
    shapes = [section(-1400., w*.74, h*.82, 13.),
              section(-1280., w*.88, h*.94, 19.),
              section(-1010., w, h, 23.),
              section(-680., middle, h, 20.),
              section(520., middle, h, 20.),
              section(spec["shoulder"], w*.91, h*.84, 19.),
              section(1280., spec["nose"]*1.14, 31., 9.),
              section(1400., spec["nose"], 13., 3.)]
    hull = bd.loft(shapes, ruled=True)
    # Blind aft recess, not a lip protruding beyond the tail face.
    bore = bd.Cylinder(29., 56., align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    bore = bore.rotate(bd.Axis.Y, 90).translate((-1401., 0, 0))
    return tag(hull - bore, "faceted_body")


def wing_blank(spec, side):
    """One real physical panel in local deployment pose; both states reuse it."""
    hx = spec["wing_x"]
    span = spec["wing_span"]
    sign = 1 if side == "starboard" else -1
    root = 14. * sign
    tip = (14. + span) * sign
    # Root chord <= 180 mm: rotating this same panel lengthwise keeps
    # its folded breadth and dorsal offset inside the 125 mm radial bound.
    chord = spec["wing_root"]
    if "waist" in spec:
        half = (14. + span*.56)*sign
        outline = [(hx-chord, root), (hx+chord, root),
                   (hx+72., half), (hx+38., tip), (hx-31., tip),
                   (hx-65., half)]
    else:
        outline = [(hx-chord, root), (hx+chord, root),
                   (hx+38., tip), (hx-31., tip)]
    wire = bd.Wire.make_polygon([(x, y, 0) for x, y in outline], close=True)
    panel = bd.extrude(bd.Face(wire), amount=3.)
    return panel.translate((0, 0, 60.))


def wing(spec, side, pose):
    panel = wing_blank(spec, side)
    if pose == "stowed":
        # Starboard parks aft and port parks forward in distinct dorsal seats.
        hinge = bd.Axis((spec["wing_x"], 14 if side == "starboard" else -14, 0), (0, 0, 1))
        panel = panel.rotate(hinge, -90.)
    return tag(panel, "wing_" + side, "#83959E")


def fin_blank(spec, angle):
    """Fin panel anchored on a fixed corner; fold rotates about X at the root."""
    theta = math.radians(angle)
    ry, rz = math.sin(theta), math.cos(theta)
    ty, tz = math.cos(theta), -math.sin(theta)
    root = 55.
    x = spec["tail_x"]
    pts = [(x-154., 0.), (x+55., 0.), (x-18., spec["tail_span"]),
           (x-132., spec["tail_span"]*.82)]
    sections = []
    for t in (-1.65, 1.65):
        sections.append(bd.Wire.make_polygon(
            [(xx, ry*(root+r)+ty*t, rz*(root+r)+tz*t) for xx, r in pts], close=True))
    return bd.Solid.make_loft(sections, ruled=True)


def fin(spec, angle, pose):
    panel = fin_blank(spec, angle)
    if pose == "stowed":
        theta = math.radians(angle)
        hinge = bd.Axis((0., 55.*math.sin(theta), 55.*math.cos(theta)), (1, 0, 0))
        fold = 75. if math.sin(theta)*math.cos(theta) > 0 else -75.
        panel = panel.rotate(hinge, fold)
    return tag(panel, "tail_fin_%03d" % angle, "#8B969A")


def rf_panels(spec):
    # The inlaid regions remain smaller than the body and do not govern the
    # silhouette. Their thickness is not a claim about actual RF equipment.
    w = spec["width"]
    for side, sign in (("port", -1), ("starboard", 1)):
        y = sign*(spec.get("waist", w)/2 - 2.5)
        yield tag(bd.Box(255., 2., 15.).translate((525., y, 0.)),
                  "flush_rf_" + side, "#72858A")


def wing_seats(spec):
    # Small permanent hinge/root bridges cross the gap between the body roof
    # and the slender wing panels; they do not fake a second folded wing.
    for side, sign in (("port", -1), ("starboard", 1)):
        seat = bd.Box(46., 29., 27.).translate((spec["wing_x"], sign*14., 51.))
        yield tag(seat, "hinge_seat_" + side, "#697D85")


def build_study(key, pose):
    if key not in STUDIES or pose not in ("deployed", "stowed"):
        raise ValueError("Unknown RDM-9 concept or pose")
    spec = STUDIES[key]
    parts = [body(spec), *rf_panels(spec), *wing_seats(spec)]
    parts += [wing(spec, side, pose) for side in ("port", "starboard")]
    parts += [fin(spec, angle, pose) for angle in (45, 135, 225, 315)]
    return bd.Compound(children=parts, label="RDM9_%s_%s_%s" % (key, spec["name"], pose))
