"""One-fin Spear shape studies; original A/Spear and its other fins are untouched."""

from cadgen import build123d as bd

from concept_shapes import (
    SEPARATION, STUDIES, cap_thruster, components, fin, profile, tag,
)


FIN_VARIANTS = {
    "Trim": dict(tip_radius=94., root_aft=18., root_fwd=218.,
                 tip_aft=95., tip_fwd=157.),
    "Rake": dict(tip_radius=95., root_aft=18., root_fwd=213.,
                 tip_aft=112., tip_fwd=146.),
    "Broad": dict(tip_radius=92., root_aft=18., root_fwd=218.,
                  tip_aft=91., tip_fwd=173.),
    # User's low trapezoid: ~83% outer/root chord with the longer bevel
    # forward (+X). Compare the earlier modest span against drawing-led height.
    "SketchSpan": dict(tip_radius=92., root_aft=18., root_fwd=218.,
                       tip_aft=28., tip_fwd=193.),
    "SketchLow": dict(tip_radius=79., root_aft=18., root_fwd=218.,
                      tip_aft=28., tip_fwd=193.),
}
TAIL_RADIUS_RATIO = .55
CAP_SHOULDER_X = -485.0


def turning_cap_boattail():
    """Flat aft end and drawn-out aft taper, with an unchanged body-side seam."""
    spec = STUDIES["A"]
    aft, seam, radius = -spec["length"]/2, -spec["length"]/2+spec["cap"], spec["radius"]
    stations = ((aft, TAIL_RADIUS_RATIO), (aft+15, .59),
                (aft+77, .85), (CAP_SHOULDER_X, 1.), (seam, .98))
    return tag(bd.Solid.make_loft(
        [profile(x, radius*ratio) for x, ratio in stations], ruled=True),
        "turning_cap", "#949EA3")


def make_revision(name, separated=False):
    assert name in FIN_VARIANTS, name
    spec = STUDIES["A"]
    seam = -spec["length"]/2+spec["cap"]
    form = FIN_VARIANTS[name]
    revised = fin(spec, 45., seam+form["root_aft"], seam+form["root_fwd"],
                  seam+form["tip_aft"], seam+form["tip_fwd"],
                  spec["fin_root"], form["tip_radius"], "aft_fin_0_prototype")
    revised.color = bd.Color(0.23, 0.35, 0.39)

    cap_spec = dict(spec, nozzle_x=.72)
    parts = []
    for part in components("A"):
        if part.label == "turning_cap":
            parts.append(turning_cap_boattail())
        elif part.label.startswith("thruster_"):
            parts.append(cap_thruster(cap_spec, int(part.label.split("_")[1])))
        elif part.label == "aft_fin_0":
            parts.append(revised)
        else:
            parts.append(part)
    if separated:
        parts = [part.moved(bd.Location((-SEPARATION, 0, 0)))
                 if part.label == "turning_cap" or part.label.startswith("thruster_")
                 else part for part in parts]
    state = "_Separated" if separated else ""
    return bd.Compound(children=parts, label=f"Spear_{name}_Boattail{state}")


def make_fin_focus(name):
    """Body plus exactly one modified fin for a fair local silhouette review."""
    model = make_revision(name)
    return bd.Compound(children=[part for part in model.children
                                 if part.label in ("body", "aft_fin_0_prototype")],
                       label=f"Spear_{name}_Fin_Focus")


def make_cap_focus():
    """The boattail and its four correctly placed thrusters in isolation."""
    model = make_revision("Trim")
    return bd.Compound(children=[part for part in model.children
                                 if part.label == "turning_cap" or part.label.startswith("thruster_")],
                       label="Spear_Boattail_Cap_Focus")


def make_selected_spear(separated=False):
    """User-approved SketchLow local fin repeated fourfold on the Spear."""
    spec = STUDIES["A"]
    form = FIN_VARIANTS["SketchLow"]
    seam = -spec["length"]/2 + spec["cap"]
    parts = [part for part in make_revision("SketchLow").children
             if not part.label.startswith("aft_fin_")]
    for index in range(4):
        angle = spec["fin_clock"] + index*90
        parts.append(fin(spec, angle, seam+form["root_aft"], seam+form["root_fwd"],
                         seam+form["tip_aft"], seam+form["tip_fwd"],
                         spec["fin_root"], form["tip_radius"], f"aft_fin_{index}"))
    if separated:
        parts = [part.moved(bd.Location((-SEPARATION, 0, 0)))
                 if part.label == "turning_cap" or part.label.startswith("thruster_")
                 else part for part in parts]
    suffix = "_Separated" if separated else ""
    return bd.Compound(children=parts, label=f"Spear_Selected_SketchLow_Boattail{suffix}")


def turning_cap_rounded():
    """Close the long boattail with an analytic rounded blunt end, no axial port."""
    spec = STUDIES["A"]
    aft, radius = -spec["length"]/2, spec["radius"]
    dome_radius = 34.
    # An actual spherical hemisphere avoids loft faceting, and unlike a smooth
    # near-point loft cannot overshoot the aft datum. The tiny 0.5 mm overlap
    # is inside the tapered forebody, yielding one continuous closed solid.
    dome = bd.Sphere(dome_radius).translate((aft+dome_radius, 0, 0))
    dome = dome & bd.Box(dome_radius+.5, 80., 80.).translate(
        (aft+(dome_radius+.5)/2, 0, 0))
    fore = bd.Solid.make_loft([
        profile(aft+dome_radius, dome_radius),
        profile(aft+77., radius*.85),
        profile(CAP_SHOULDER_X, radius),
        profile(aft+spec["cap"], radius*.98),
    ], ruled=True)
    return tag(dome.fuse(fore), "turning_cap", "#949EA3")


def make_rounded_cap_preview(separated=False, cap_only=False):
    """Selected four-fin Spear, replacing only the historical flat-ended cap."""
    model = make_selected_spear()
    parts = [turning_cap_rounded() if part.label == "turning_cap" else part
             for part in model.children]
    if cap_only:
        parts = [part for part in parts
                 if part.label == "turning_cap" or part.label.startswith("thruster_")]
    elif separated:
        parts = [part.moved(bd.Location((-SEPARATION, 0, 0)))
                 if part.label == "turning_cap" or part.label.startswith("thruster_")
                 else part for part in parts]
    suffix = "_Cap_Focus" if cap_only else ("_Separated" if separated else "")
    return bd.Compound(children=parts, label=f"Spear_RoundedTip_Boattail{suffix}")
