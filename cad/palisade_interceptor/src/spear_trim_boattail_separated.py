"""Separated-cap view of the Trim fin prototype."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_Trim_Boattail_Separated.step")
def spear_trim_boattail_separated():
    return make_revision("Trim", separated=True)

if __name__ == "__main__":
    spear_trim_boattail_separated()
