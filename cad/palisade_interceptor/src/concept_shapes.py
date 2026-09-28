"""Three geometry-only Palisade interceptor studies (millimetres, +X nose).

Four cardinal nozzles belong to a separable aft turning cap. The exposed main
nozzle belongs to the body. Geometry here describes only appearance, not flight.
"""

import math

from cadgen import build123d as bd, srgb


STUDIES = {
    "A": dict(name="Spear", length=1200., radius=62., cap=180., nose=245.,
              section="round", tail=.76, fin_root=55., fin_tip=101.,
              fin_aft=18., fin_fwd=218., fin_tip_aft=95., fin_tip_fwd=157.,
              fin_clock=45., canards=False, nozzle_x=.53),
    "B": dict(name="Shoulder", length=1120., radius=73., cap=215., nose=147.,
              section="round", tail=.96, fin_root=67., fin_tip=88.,
              fin_aft=36., fin_fwd=170., fin_tip_aft=66., fin_tip_fwd=124.,
              fin_clock=0., canards=True, nozzle_x=.45),
    "C": dict(name="Facet", length=1280., radius=66., cap=230., nose=225.,
              section="octagonal", tail=.76, fin_root=56., fin_tip=103.,
              fin_aft=22., fin_fwd=185., fin_tip_aft=83., fin_tip_fwd=140.,
              fin_clock=45., canards=False, nozzle_x=.53),
}
SEPARATION = 270.0


def tag(shape, name, color="#A6AFB2"):
    shape.label = name
    shape.color = srgb(color)
    return shape


def profile(x, radius, section="round"):
    plane = bd.Plane(origin=(x, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    if section == "round":
        return bd.Wire.make_circle(radius, plane)
    # Clock the octagon to make dorsal and ventral faces and four distinct chines.
    vertices = [
        (x, radius * math.cos(math.pi * (i + .5) / 4),
         radius * .88 * math.sin(math.pi * (i + .5) / 4))
        for i in range(8)
    ]
    return bd.Wire.make_polygon(vertices, close=True)


def cylinder(x0, x1, radius):
    return (bd.Cylinder(radius, x1 - x0,
                        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
            .rotate(bd.Axis.Y, 90).translate((x0, 0, 0)))


def body(spec):
    tail, nose, r = -spec["length"] / 2 + spec["cap"], spec["length"] / 2, spec["radius"]
    base = nose - spec["nose"]
    if spec["name"] == "Spear":
        stations = [(tail, spec.get("aft_radius_ratio", .98)), (tail+22, 1.), (tail+165, .92),
                    (base-165, .89), (base, .88), (base+spec["nose"]*.44, .61),
                    (base+spec["nose"]*.78, .28), (nose, .024)]
    elif spec["name"] == "Shoulder":
        stations = [(tail, .99), (tail+23, 1.08), (tail+96, 1.08),
                    (base-155, 1.), (base, .99), (base+spec["nose"]*.5, .79),
                    (base+spec["nose"]*.85, .36), (nose, .026)]
    else:
        stations = [(tail, 1.), (tail+30, 1.), (tail+175, .92),
                    (base-160, .89), (base, .89), (base+spec["nose"]*.52, .68),
                    (base+spec["nose"]*.84, .29), (nose, .03)]
    shell = bd.Solid.make_loft([profile(x, r*scale, spec["section"]) for x, scale in stations], ruled=True)
    # This cavity is part of the body, so the aft nozzle is exposed on release.
    cavity = cylinder(tail-1, tail+53, r*.61)
    return tag(shell - cavity, "body")


def cap(spec):
    aft, seam, r = -spec["length"]/2, -spec["length"]/2+spec["cap"], spec["radius"]
    stations = [(aft, spec["tail"]), (aft+20, spec["tail"]+.06),
                (aft+spec["cap"]*.54, 1.), (seam, .98 if spec["name"] == "Spear" else (1. if spec["name"] == "Facet" else .99))]
    return tag(bd.Solid.make_loft(
        [profile(x, r*scale, spec["section"]) for x, scale in stations], ruled=True),
        "turning_cap", "#949EA3")


def main_nozzle(spec):
    seam, r = -spec["length"]/2+spec["cap"], spec["radius"]
    outer = cylinder(seam, seam+12, r*.56)
    bore = cylinder(seam-1, seam+14, r*.35)
    return tag(outer - bore, "main_nozzle", "#30383B")


def cap_thruster(spec, angle):
    seam, r = -spec["length"]/2+spec["cap"], spec["radius"]
    a = math.radians(angle)
    x = -spec["length"]/2 + spec["cap"]*spec["nozzle_x"]
    # Faceted ventral/dorsal flats sit below the nominal circumradius; inset
    # their thruster roots so all four housings actually intersect the cap.
    distance = r * (.91 if spec["name"] == "Facet" else 1.03)
    outer = bd.Cylinder(10.5, 18, align=(bd.Align.CENTER,)*3)
    bore = bd.Cylinder(6.6, 20, align=(bd.Align.CENTER,)*3)
    tube = (outer - bore).rotate(bd.Axis.X, 90-angle)
    return tag(tube.translate((x, distance*math.cos(a), distance*math.sin(a))),
               f"thruster_{angle}", "#323A3E")


def fin(spec, angle, root_aft, root_fwd, tip_aft, tip_fwd, root_r, tip_r, label,
        root_thickness=7., tip_thickness=2.4):
    a = math.radians(angle)
    radial = (0., math.cos(a), math.sin(a))
    tangent = (0., -math.sin(a), math.cos(a))

    def wire(x0, x1, radius, thickness):
        return bd.Wire.make_polygon([
            (x, radius*radial[1]-thickness*tangent[1]/2,
             radius*radial[2]-thickness*tangent[2]/2)
            for x in (x0, x1)
        ] + [
            (x, radius*radial[1]+thickness*tangent[1]/2,
             radius*radial[2]+thickness*tangent[2]/2)
            for x in (x1, x0)
        ], close=True)

    return tag(bd.Solid.make_loft([
        wire(root_aft, root_fwd, root_r, root_thickness),
        wire(tip_aft, tip_fwd, tip_r, tip_thickness),
    ], ruled=True), label, "#717F84")


def components(key):
    spec = STUDIES[key]
    seam = -spec["length"]/2 + spec["cap"]
    parts = [body(spec), cap(spec), main_nozzle(spec)]
    for angle in (0, 90, 180, 270):
        parts.append(cap_thruster(spec, angle))
    for i in range(4):
        angle = spec["fin_clock"] + i*90
        parts.append(fin(spec, angle, seam+spec["fin_aft"], seam+spec["fin_fwd"],
                         seam+spec["fin_tip_aft"], seam+spec["fin_tip_fwd"],
                         spec["fin_root"], spec["fin_tip"], f"aft_fin_{i}"))
    if spec["canards"]:
        for i in range(4):
            angle = 45+i*90
            parts.append(fin(spec, angle, 220., 325., 255., 293.,
                             72., 91., f"fore_fin_{i}"))
    return parts


def make_study(key, separated=False):
    parts = components(key)
    if separated:
        parts = [part.moved(bd.Location((-SEPARATION, 0, 0)))
                 if part.label == "turning_cap" or part.label.startswith("thruster_")
                 else part for part in parts]
    suffix = "_Separated" if separated else ""
    return bd.Compound(children=parts, label=f"Palisade_{key}_{STUDIES[key]['name']}{suffix}")
