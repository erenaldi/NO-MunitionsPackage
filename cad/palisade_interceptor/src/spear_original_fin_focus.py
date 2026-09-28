"""Unmodified A/Spear fin and main body for matched local review."""
from cadgen import build123d as bd, step
from concept_shapes import components

@step(out="../STEP/Spear_Original_Fin_Focus.step")
def spear_original_fin_focus():
    return bd.Compound(children=[part for part in components("A")
                                 if part.label in ("body", "aft_fin_0")],
                       label="Spear_Original_Fin_Focus")

if __name__ == "__main__":
    spear_original_fin_focus()
