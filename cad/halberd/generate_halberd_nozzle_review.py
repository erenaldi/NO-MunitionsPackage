"""Close-review model for the AAM-44 Halberd booster nozzle, extracted from the master."""

from pathlib import Path

from cadgen import build123d as bd
from cadgen import read_step, step

SOURCE = Path(__file__).with_name("AAM-44_Halberd_Detailed.step")


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


@step(out="AAM-44_Halberd_Nozzle_Review.step")
def halberd_nozzle_review():
    model = read_step(SOURCE)
    cutter = bd.Box(283.5, 220.0, 220.0).translate((-1541.75, 0.0, 0.0), transform=True)
    children = []
    for part in model.children:
        if part.label.startswith("booster_nozzle_"):
            children.append(part)
        elif part.label == "booster_body":
            clipped = _clip(part, cutter)
            if clipped is not None:
                children.append(clipped)
    return bd.Compound(children=children, label="AAM-44_Halberd_Nozzle_Review")


if __name__ == "__main__":
    halberd_nozzle_review()
