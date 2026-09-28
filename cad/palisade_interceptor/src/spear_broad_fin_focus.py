"""Local view of just body and Broad fin."""
from cadgen import step
from spear_revision_shapes import make_fin_focus

@step(out="../STEP/Spear_Broad_Fin_Focus.step")
def spear_broad_fin_focus():
    return make_fin_focus("Broad")

if __name__ == "__main__":
    spear_broad_fin_focus()
