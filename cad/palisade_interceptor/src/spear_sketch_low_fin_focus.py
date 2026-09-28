"""Isolate the body and one image-led low-profile fin."""
from cadgen import step
from spear_revision_shapes import make_fin_focus

@step(out="../STEP/Spear_SketchLow_Fin_Focus.step")
def spear_sketch_low_fin_focus():
    return make_fin_focus("SketchLow")

if __name__ == "__main__":
    spear_sketch_low_fin_focus()
