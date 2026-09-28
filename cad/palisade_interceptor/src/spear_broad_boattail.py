"""Spear local review: shorter span with a longer cropped tip."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_Broad_Boattail.step")
def spear_broad_boattail():
    return make_revision("Broad")

if __name__ == "__main__":
    spear_broad_boattail()
