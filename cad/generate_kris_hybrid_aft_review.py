"""Rear close-up extracted from the tail-only Kris/PL-10 hybrid."""

from pathlib import Path

from cadgen import build123d as bd, read_step, step


@step(out="IRM-S4_Kris_Hybrid_Aft_Review.step")
def aft_review():
    model = read_step(Path(__file__).with_name("IRM-S4_Kris_PL10_Hybrid.step"))
    parts = [part for part in model.children if part.label.startswith(
        ("kris_grid_", "grid_", "tvc_", "aft_end_cover", "aft_collar_edge_rim_", "aft_dark_recess")
    ) or part.label == "body_section_1"]
    if not parts:
        raise ValueError("No hybrid aft parts found")
    return bd.Compound(children=parts, label="Kris_Hybrid_Aft_Review")


if __name__ == "__main__":
    aft_review()
