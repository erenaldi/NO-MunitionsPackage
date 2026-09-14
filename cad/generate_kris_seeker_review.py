"""Hybrid seeker review with the same polished-window material as the full model."""

from pathlib import Path

from cadgen import build123d as bd, read_step, step
from generate_kris_hybrid import SEEKER_WINDOW_MATERIAL


@step(out="Kris_Hybrid_Seeker_Review.step")
def seeker_review():
    model = read_step(Path(__file__).with_name("IRM-S4_Kris_PL10_Hybrid.step"))
    parts = [part for part in model.children if part.label.startswith("seeker_")
             or part.label in ("rounded_nose_housing", "nose_window_rim", "dark_nose_window")]
    window = next(part for part in parts if part.label == "dark_nose_window")
    # STEP carries geometry/colors; reapply the authoring material for this review.
    window.cad_material = dict(SEEKER_WINDOW_MATERIAL)
    return bd.Compound(children=parts, label="Kris_Hybrid_Polished_Seeker")


if __name__ == "__main__":
    seeker_review()
