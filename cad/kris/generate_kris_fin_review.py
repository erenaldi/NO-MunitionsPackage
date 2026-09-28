"""Isolated top-view review of the single hexagonal-lattice fin prototype."""

from pathlib import Path

from cadgen import read_step, step


@step(out="Kris_Grid_Fin_Prototype.step")
def fin_review():
    model = read_step(Path(__file__).with_name("IRM-S4_Kris_PL10_Hybrid.step"))
    return next(part for part in model.children if part.label == "kris_grid_fin_2")


if __name__ == "__main__":
    fin_review()
