from cadgen import step
from study_shapes import build_study


@step(out="../STEP/B_Shoulder_Deployed.step")
def model():
    return build_study("B", "deployed")


if __name__ == "__main__":
    model()
