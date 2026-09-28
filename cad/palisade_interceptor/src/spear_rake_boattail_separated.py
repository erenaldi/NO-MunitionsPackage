"""Separated-cap view of the Rake fin prototype."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_Rake_Boattail_Separated.step")
def spear_rake_boattail_separated():
    return make_revision("Rake", separated=True)

if __name__ == "__main__":
    spear_rake_boattail_separated()
