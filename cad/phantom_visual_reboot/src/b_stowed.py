from cadgen import step
from study_shapes import build_study


@step(out="../STEP/B_Shoulder_Stowed.step")
def model():
    return build_study("B", "stowed")


if __name__ == "__main__":
    model()
