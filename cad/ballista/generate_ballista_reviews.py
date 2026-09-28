"""Diagnostic derivatives of the primary Ballista STEPs, never release masters.

Cuts are deliberately capped CAD solids. Three wing poses are displayed apart
for review only; translations are not runtime placements.
"""

from pathlib import Path

from cadgen import build123d as bd, read_step, step
from ballista_geometry import WING_PIVOT_X, WING_PIVOT_Y, WING_PIVOT_Z, WING_ANGLE, INTAKE_X

ROOT = Path(__file__).parent


def _source():
    return read_step(ROOT / "AGM-110_Ballista_Stowed.step")


def _clip(part, cutter):
    shape = part.intersect(cutter)
    if shape is None:
        return None
    solids = [s for s in shape.solids() if s.volume > 1e-6]
    if not solids:
        return None
    for index, solid in enumerate(solids):
        solid.label = part.label if len(solids) == 1 else f"{part.label}_{index+1}"
        solid.color = part.color
    return solids[0] if len(solids) == 1 else bd.Compound(label=part.label, children=solids)


def _region(x, length, label, half=False):
    cutter = bd.Box(length, 500 if not half else 250, 500).translate(
        (x,0 if not half else -125,0))
    children = []
    for p in _source().children:
        if p.bounding_box().max.X < x-length/2 or p.bounding_box().min.X > x+length/2:
            continue
        cut = _clip(p,cutter)
        if cut is not None:
            children.append(cut)
    return bd.Compound(label=label, children=children)


@step(out="Ballista_Seeker_Review.step")
def ballista_seeker_review():
    return _region(1160, 330, "Ballista seeker crop")


@step(out="Ballista_Propulsion_Review.step")
def ballista_propulsion_review():
    return _region(-1160, 330, "Ballista propulsion crop")


@step(out="Ballista_Propulsion_Section.step")
def ballista_propulsion_section():
    return _region(-1160, 330, "Ballista propulsion half section", half=True)


@step(out="Ballista_Mount_Review.step")
def ballista_mount_review():
    cutter = bd.Box(1100,200,100).translate((0,0,150))
    parts = []
    for p in _source().children:
        if p.label not in {"Body","MountRail","ForwardLug","AftLug","DorsalUmbilicalCover"}:
            continue
        clipped = _clip(p,cutter)
        if clipped is not None:
            parts.append(clipped)
    return bd.Compound(label="Ballista dorsal mounting crop",children=parts)


@step(out="Ballista_Wing_Deployment_Review.step")
def ballista_wing_deployment_review():
    source = {p.label:p for p in _source().children}
    modules = []
    for angle, offset in ((0,-1400),(WING_ANGLE/2,0),(WING_ANGLE,1400)):
        children = []
        for name in ("Left","Right"):
            side = -1 if name == "Left" else 1
            axis = bd.Axis((WING_PIVOT_X,side*WING_PIVOT_Y,WING_PIVOT_Z),(0,0,1))
            for suffix in ("", "PivotCap"):
                part = source[f"Wing{name}{suffix}"].rotate(axis,-side*angle)
                children.append(part)
            children.append(source[f"WingBay{name}"].moved(bd.Location((0,0,0))))
        modules.append(bd.Compound(label=f"Wing pose {angle:g} degrees",children=children)
                       .translate((0,offset,0)))
    return bd.Compound(label=f"Ballista 0 / {WING_ANGLE/2:g} / {WING_ANGLE:g} degree wing deployment",children=modules)


@step(out="Ballista_Wing_Root_Review.step")
def ballista_wing_root_review():
    cutter = bd.Box(230,180,100).translate((WING_PIVOT_X,WING_PIVOT_Y,WING_PIVOT_Z))
    children = []
    for part in _source().children:
        if part.label in {"Body","WingRight","WingRightPivotCap","WingBayRight"}:
            clipped = _clip(part,cutter)
            if clipped is not None:
                children.append(clipped)
    return bd.Compound(label="Ballista right wing hinge crop",children=children)


@step(out="Ballista_Intake_Review.step")
def ballista_intake_review():
    cutter = bd.Box(242,66,124).translate((INTAKE_X,137,0))
    children = []
    for part in _source().children:
        if part.label == "Body" or part.label == "AftServiceRight" or part.label.startswith(
                ("IntakeRight","PanelFastenerRight_-")):
            clipped = _clip(part,cutter)
            if clipped is not None:
                children.append(clipped)
    return bd.Compound(label="Ballista right recessed intake",children=children)


@step(out="Ballista_Wing_Recess_Review.step")
def ballista_wing_recess_review():
    """Expose the smooth hull pockets without wings obscuring their floor blends."""
    body = next(p for p in _source().children if p.label == "Body")
    cutter = bd.Box(1160,400,90).translate((-65,0,-148))
    return _clip(body,cutter)


@step(out="Ballista_Intake_Section.step")
def ballista_intake_section():
    cutter = bd.Box(242,66,62).translate((INTAKE_X,137,-31))
    children = []
    for part in _source().children:
        if part.label in {"Body","AftServiceRight"} or part.label.startswith("IntakeRight"):
            clipped = _clip(part,cutter)
            if clipped is not None:
                children.append(clipped)
    return bd.Compound(label="Ballista intake half section",children=children)


if __name__ == "__main__":
    ballista_seeker_review()
    ballista_propulsion_review()
    ballista_propulsion_section()
    ballista_mount_review()
    ballista_wing_deployment_review()
    ballista_wing_root_review()
    ballista_wing_recess_review()
    ballista_intake_review()
    ballista_intake_section()
