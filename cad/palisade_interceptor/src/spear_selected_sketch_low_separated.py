"""Selected four-fin Spear with review-only translated turning cap."""
from cadgen import step
from spear_revision_shapes import make_selected_spear

@step(out="../STEP/Spear_Selected_SketchLow_Boattail_Separated.step")
def spear_selected_sketch_low_separated():
    return make_selected_spear(separated=True)

if __name__ == "__main__":
    spear_selected_sketch_low_separated()
