"""Image-led long trapezoid with earlier modest fin span; one station only."""
from cadgen import step
from spear_revision_shapes import make_revision

@step(out="../STEP/Spear_SketchSpan_Boattail.step")
def spear_sketch_span_boattail():
    return make_revision("SketchSpan")

if __name__ == "__main__":
    spear_sketch_span_boattail()
