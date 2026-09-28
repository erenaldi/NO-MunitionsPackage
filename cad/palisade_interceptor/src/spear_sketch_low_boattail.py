"""Image-led long, lower-profile trapezoid; one station only."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_SketchLow_Boattail.step")
def spear_sketch_low_boattail():
    return make_revision("SketchLow")

if __name__ == "__main__":
    spear_sketch_low_boattail()
