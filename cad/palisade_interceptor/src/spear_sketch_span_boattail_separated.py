"""Image-led SketchSpan with cap translated for visual review."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_SketchSpan_Boattail_Separated.step")
def spear_sketch_span_boattail_separated():
    return make_revision("SketchSpan", separated=True)

if __name__ == "__main__":
    spear_sketch_span_boattail_separated()
