"""Selected Spear: four image-led low fins and full turning-cap boattail."""
from cadgen import step
from spear_revision_shapes import make_selected_spear

@step(out="../STEP/Spear_Selected_SketchLow_Boattail.step")
def spear_selected_sketch_low():
    return make_selected_spear()

if __name__ == "__main__":
    spear_selected_sketch_low()
