"""Isolated close-review model for one AAM-44 Halberd intake module."""

from cadgen import build123d as bd
from cadgen import step

from generate_halberd_detailed import (
    make_intake_parts,
    make_sustainer_fin,
)


@step(out="AAM-44_Halberd_Intake_Review.step")
def halberd_intake_review():
    parts = [*make_intake_parts(1, 0.0), make_sustainer_fin(1, 0.0)]
    return bd.Compound(children=parts, label="AAM-44_Halberd_Intake_Review")


if __name__ == "__main__":
    halberd_intake_review()
