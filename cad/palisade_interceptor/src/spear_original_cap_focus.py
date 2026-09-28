"""Unmodified A/Spear cap and its thrusters for matched boattail review."""
from cadgen import build123d as bd, step
from concept_shapes import components

@step(out="../STEP/Spear_Original_Cap_Focus.step")
def spear_original_cap_focus():
    return bd.Compound(children=[part for part in components("A")
                                 if part.label == "turning_cap" or part.label.startswith("thruster_")],
                       label="Spear_Original_Cap_Focus")

if __name__ == "__main__":
    spear_original_cap_focus()
