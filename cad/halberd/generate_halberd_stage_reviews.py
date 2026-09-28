"""Isolated flight-state review models for the detailed Halberd."""

from pathlib import Path

from cadgen import build123d as bd
from cadgen import read_step, step


SOURCE = Path(__file__).with_name("AAM-44_Halberd_Detailed.step")


def is_booster(label):
    return label.startswith("booster_")


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


@step(out="AAM-44_Halberd_UpperStage_Review.step")
def halberd_upper_stage_review():
    model = read_step(SOURCE)
    parts = [part for part in model.children if not is_booster(part.label)]
    return bd.Compound(children=parts, label="AAM-44_Halberd_UpperStage")


@step(out="AAM-44_Halberd_Booster_Review.step")
def halberd_booster_review():
    model = read_step(SOURCE)
    parts = [part for part in model.children if is_booster(part.label)]
    return bd.Compound(children=parts, label="AAM-44_Halberd_Booster")


@step(out="AAM-44_Halberd_SustainerSeam_Review.step")
def halberd_sustainer_seam_review():
    """Focused sustainer nozzle and stage seam with cropped body context."""
    model = read_step(SOURCE)
    cutter = bd.Box(200.0, 220.0, 220.0).translate((-320.0, 0.0, 0.0), transform=True)
    children = []
    for part in model.children:
        if part.label in ("sustainer_nozzle", "stage_joint_band", "booster_forward_collar"):
            children.append(part)
        elif part.label in ("ramjet_body", "booster_body"):
            clipped = _clip(part, cutter)
            if clipped is not None:
                children.append(clipped)
    return bd.Compound(children=children, label="AAM-44_Halberd_SustainerSeam_Review")


@step(out="AAM-44_Halberd_SustainerNozzle_Review.step")
def halberd_sustainer_nozzle_review():
    model = read_step(SOURCE)
    cutter = bd.Box(120.0, 240.0, 240.0).translate((-276.7, 0, 0), transform=True)
    children = []
    for part in model.children:
        if part.label in ("sustainer_nozzle", "stage_joint_band"):
            children.append(part)
        elif part.label == "ramjet_body":
            children.append(_clip(part, cutter))
    return bd.Compound(children=children, label="Halberd_exposed_sustainer_nozzle")


@step(out="AAM-44_Halberd_Separated_Review.step")
def halberd_separated_review():
    # Display-only separation; production pivot and all source parts are unchanged.
    model = read_step(SOURCE)
    children = [part.moved(bd.Location((-350, 0, 0))) if is_booster(part.label)
                else part for part in model.children]
    return bd.Compound(children=children, label="Halberd_separated_display_350mm")


if __name__ == "__main__":
    halberd_upper_stage_review()
    halberd_booster_review()
    halberd_sustainer_seam_review()
    halberd_sustainer_nozzle_review()
    halberd_separated_review()
