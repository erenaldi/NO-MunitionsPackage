"""Image-led SketchLow with cap translated for visual review."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_SketchLow_Boattail_Separated.step")
def spear_sketch_low_boattail_separated():
    return make_revision("SketchLow", separated=True)

if __name__ == "__main__":
    spear_sketch_low_boattail_separated()
