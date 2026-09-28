"""Isolate the body and one image-led modest-span fin."""
from cadgen import step
from spear_revision_shapes import make_fin_focus

@step(out="../STEP/Spear_SketchSpan_Fin_Focus.step")
def spear_sketch_span_fin_focus():
    return make_fin_focus("SketchSpan")

if __name__ == "__main__":
    spear_sketch_span_fin_focus()
