"""Spear local review: a narrow, raked tip."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_Rake_Boattail.step")
def spear_rake_boattail():
    return make_revision("Rake")

if __name__ == "__main__":
    spear_rake_boattail()
