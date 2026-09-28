from cadgen import step
from study_shapes import build_study


@step(out="../STEP/A_Facet_Stowed.step")
def model():
    return build_study("A", "stowed")


if __name__ == "__main__":
    model()
