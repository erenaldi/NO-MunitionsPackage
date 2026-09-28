"""Spear local review: original planform with slightly reduced span."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_Trim_Boattail.step")
def spear_trim_boattail():
    return make_revision("Trim")

if __name__ == "__main__":
    spear_trim_boattail()
