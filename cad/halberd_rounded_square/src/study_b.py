from cadgen import step
from study_shapes import build_study

@step(out="../STEP/B_Chine.step")
def study_b():
    return build_study("B")

if __name__ == "__main__":
    study_b()
