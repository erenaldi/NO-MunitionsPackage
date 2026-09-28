from cadgen import step
from sketch_nose_r1_shapes import build


@step(out="../STEP/D_SketchNose_R1_Stowed.step")
def model():
    return build("stowed")


if __name__ == "__main__":
    model()
