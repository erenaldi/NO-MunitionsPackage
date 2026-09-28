"""Close-review models for one AAM-44 Halberd intake module, extracted from the master."""

from pathlib import Path

from cadgen import build123d as bd
from cadgen import read_step, step

SOURCE = Path(__file__).with_name("AAM-44_Halberd_Detailed.step")

MODULE_LABELS = (
    "intake_ramp_1",
    "intake_lip_1",
    "intake_duct_1",
    "intake_cheek_1_1",
    "intake_cheek_1_2",
    "sustainer_fin_1",
)
BODY_LABELS = ("ramjet_body", "ramjet_joint_band", "forward_body", "forward_joint_band")


def _module_parts(model):
    parts = [part for part in model.children if part.label in MODULE_LABELS]
    if len(parts) != len(MODULE_LABELS):
        raise ValueError("Intake module 1 parts not found in the master STEP")
    # Module 1 is authored at azimuth 60; unrotate +60 to the dorsal reference.
    return [part.rotate(bd.Axis.X, 60.0) for part in parts]


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


@step(out="AAM-44_Halberd_Intake_Review.step")
def halberd_intake_review():
    """Isolated module 1 (unrotated to dorsal) for passage, mouth, and grazing views."""
    model = read_step(SOURCE)
    return bd.Compound(children=_module_parts(model), label="AAM-44_Halberd_Intake_Review")


@step(out="AAM-44_Halberd_Intake_Context_Review.step")
def halberd_intake_context_review():
    """Module 1 unrotated to dorsal with a cropped contextual body."""
    model = read_step(SOURCE)
    cutter = bd.Box(1130.0, 360.0, 360.0).translate((245.0, 0.0, 0.0), transform=True)
    children = _module_parts(model)
    for part in model.children:
        if part.label not in BODY_LABELS:
            continue
        clipped = _clip(part, cutter)
        if clipped is not None:
            children.append(clipped)
    return bd.Compound(children=children, label="AAM-44_Halberd_Intake_Context_Review")


if __name__ == "__main__":
    halberd_intake_review()
    halberd_intake_context_review()
