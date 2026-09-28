from cadgen import step
from study_shapes import build_study


@step(out="../STEP/A_Facet_Deployed.step")
def model():
    return build_study("A", "deployed")


if __name__ == "__main__":
    model()
