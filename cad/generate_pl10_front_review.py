"""Forward-section review extracted from the full PL-10 STEP."""

from pathlib import Path

from cadgen import build123d as bd, read_step, step


@step(out="PL-10_Front_Review.step")
def front_review():
    model = read_step(Path(__file__).with_name("PL-10_Stencil_Revision.step"))
    parts = [part for part in model.children if part.bounding_box().min.Z >= 1980]
    if not parts:
        raise ValueError("No forward parts found")
    return bd.Compound(children=parts, label="PL10_Forward_Exterior_Review")


if __name__ == "__main__":
    front_review()
