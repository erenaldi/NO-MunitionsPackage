"""Isolated flight-state review models for the detailed Halberd."""

from pathlib import Path

from cadgen import build123d as bd
from cadgen import read_step, step


SOURCE = Path(__file__).with_name("AAM-44_Halberd_Detailed.step")


def is_booster(label):
    return label.startswith("booster_")


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


if __name__ == "__main__":
    halberd_upper_stage_review()
    halberd_booster_review()
