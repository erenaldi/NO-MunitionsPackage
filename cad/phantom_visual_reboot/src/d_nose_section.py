from cadgen import step
from sketch_nose_r1_shapes import section_slab


@step(out="../STEP/D_SketchNose_R1_NoseSection.step")
def model():
    return section_slab(1160)


if __name__ == "__main__":
    model()
