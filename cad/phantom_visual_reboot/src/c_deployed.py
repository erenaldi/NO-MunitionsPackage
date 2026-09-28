from cadgen import step
from study_shapes import build_study


@step(out="../STEP/C_Keel_Deployed.step")
def model():
    return build_study("C", "deployed")


if __name__ == "__main__":
    model()
