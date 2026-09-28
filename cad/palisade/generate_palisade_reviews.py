"""Separated flight-state review model for the HKP-1 Palisade."""

from pathlib import Path

from cadgen import build123d as bd
from cadgen import read_step, step


SOURCE = Path(__file__).with_name("HKP-1_Palisade_Interceptor.step")


def is_cap_part(label):
    return label == "turning_cap" or label.startswith("nozzle_")


@step(out="HKP-1_Palisade_Separated_Review.step")
def palisade_separated_review():
    # Display-only separation; the production datums and source parts are unchanged.
    model = read_step(SOURCE)
    children = [
        part.moved(bd.Location((-220.0, 0.0, 0.0))) if is_cap_part(part.label) else part
        for part in model.children
    ]
    return bd.Compound(children=children, label="HKP-1_Palisade_Separated_Review")


if __name__ == "__main__":
    palisade_separated_review()
