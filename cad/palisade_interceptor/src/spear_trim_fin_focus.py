"""Local view of just body and Trim fin."""
from cadgen import step
from spear_revision_shapes import make_fin_focus

@step(out="../STEP/Spear_Trim_Fin_Focus.step")
def spear_trim_fin_focus():
    return make_fin_focus("Trim")

if __name__ == "__main__":
    spear_trim_fin_focus()
