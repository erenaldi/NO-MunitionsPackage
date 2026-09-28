"""Seeker-housing review extracted from the full PL-10 STEP."""

from pathlib import Path

from cadgen import build123d as bd, read_step, step


@step(out="PL-10_Seeker_Review.step")
def seeker_review():
    model = read_step(Path(__file__).with_name("PL-10_Stencil_Revision.step"))
    parts = [part for part in model.children if part.label.startswith("seeker_")
             or part.label in ("rounded_nose_housing", "nose_window_rim", "dark_nose_window")]
    if not parts:
        raise ValueError("No seeker parts found")
    return bd.Compound(children=parts, label="PL10_Seeker_Exterior_Review")


if __name__ == "__main__":
    seeker_review()
