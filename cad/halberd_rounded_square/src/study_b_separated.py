from cadgen import step
from study_shapes import build_study

@step(out="../STEP/B_Chine_Separated.step")
def study_b_separated():
    return build_study("B", separated=True)

if __name__ == "__main__":
    study_b_separated()
