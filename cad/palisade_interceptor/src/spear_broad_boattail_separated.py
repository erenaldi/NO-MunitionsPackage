"""Separated-cap view of the Broad fin prototype."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_Broad_Boattail_Separated.step")
def spear_broad_boattail_separated():
    return make_revision("Broad", separated=True)

if __name__ == "__main__":
    spear_broad_boattail_separated()
