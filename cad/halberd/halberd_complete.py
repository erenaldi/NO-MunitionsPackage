from pathlib import Path

from cadgen import build123d as bd
from cadgen import read_step, step

from clean_booster import clean_booster


UPPER_STAGE_SOURCE = Path(r"C:\Users\erena\Downloads\Halberd_UpperStage V2.step")


@step(out="Halberd_Complete.step")
def halberd_complete():
    upper_stage = read_step(UPPER_STAGE_SOURCE)
    upper_stage.label = "upper_stage"

    booster = clean_booster()
    booster.label = "booster"

    return bd.Compound(children=[upper_stage, booster], label="AAM-44_Halberd")


if __name__ == "__main__":
    halberd_complete()
