"""Read-only rigid reorientation of the selected Kris for a +X-forward comparison."""
from pathlib import Path
from cadgen import build123d as bd, read_step, step

SOURCE = Path(__file__).resolve().parents[2] / "IRM-S4_Kris_PL10_Hybrid.step"


@step(out="../STEP/kris_full_reference.step")
def kris_full_reference():
    original = read_step(SOURCE)
    parts = []
    for part in original.children:
        placed = part.rotate(bd.Axis.Y, 90.)
        placed.label = part.label
        placed.color = part.color
        parts.append(placed)
    if len(parts) != 270:
        raise ValueError("Selected Kris inventory changed; review reference selection")
    return bd.Compound(children=parts, label="Kris_Hybrid_Whole_Reference_X_Forward")


if __name__ == "__main__":
    kris_full_reference()
