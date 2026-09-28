from pathlib import Path

from cadgen import build123d as bd
from cadgen import glb, read_step, step, stl


SOURCE = Path(r"C:\Users\erena\Downloads\Halberd_Booster_Cylinder V1.step")


@step(out="Halberd_Booster_Clean.step")
@stl(out="Halberd_Booster_Clean.stl")
@glb(out="Halberd_Booster_Clean.glb")
def clean_booster():
    imported = read_step(SOURCE)
    solids = list(imported.solids())
    if len(solids) != 4:
        raise ValueError(f"Expected four overlapping booster solids, found {len(solids)}")

    booster = solids[0].fuse(*solids[1:]).clean().rotate(bd.Axis.X, 45)
    booster.label = "booster"
    return booster


if __name__ == "__main__":
    clean_booster()
