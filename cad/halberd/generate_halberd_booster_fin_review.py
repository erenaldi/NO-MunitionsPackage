"""Close-review model for one AAM-44 Halberd booster-fin module, extracted from the master."""

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


@step(out="AAM-44_Halberd_BoosterFin_Review.step")
def halberd_booster_fin_review():
    model = read_step(SOURCE)
    cutter = bd.Box(1060.0, 440.0, 440.0).translate((-1030.0, 0.0, 0.0), transform=True)
    children = []
    for part in model.children:
        if part.label in ("booster_fin_1", "booster_fin_root_1"):
            # Fin 1 is authored at azimuth 60; unrotate +60 to the dorsal reference.
            children.append(part.rotate(bd.Axis.X, 60.0))
        elif part.label == "booster_body":
            clipped = _clip(part, cutter)
            if clipped is not None:
                children.append(clipped)
    return bd.Compound(children=children, label="AAM-44_Halberd_BoosterFin_Review")


if __name__ == "__main__":
    halberd_booster_fin_review()
