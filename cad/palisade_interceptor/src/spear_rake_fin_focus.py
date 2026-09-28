"""Local view of just body and Rake fin."""
from cadgen import step
from spear_revision_shapes import make_fin_focus

@step(out="../STEP/Spear_Rake_Fin_Focus.step")
def spear_rake_fin_focus():
    return make_fin_focus("Rake")

if __name__ == "__main__":
    spear_rake_fin_focus()
