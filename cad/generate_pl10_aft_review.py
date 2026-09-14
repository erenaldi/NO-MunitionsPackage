"""Detail-review artifact extracted from the generated full PL-10 STEP."""

from pathlib import Path

from cadgen import build123d as bd, read_step, step


@step(out="PL-10_Aft_Review.step")
def aft_review():
    model = read_step(Path(__file__).with_name("PL-10_Stencil_Revision.step"))
    parts = [part for part in model.children if part.label.startswith(
        ("stepped_tail_fin_", "tail_mount_", "tvc_", "aft_end_cover", "aft_collar_edge_rim_", "aft_dark_recess")
    ) or part.label == "body_section_1"]
    if not parts:
        raise ValueError("No aft review parts found in the full STEP")
    return bd.Compound(children=parts, label="PL10_Aft_Exterior_Review")


if __name__ == "__main__":
    aft_review()
