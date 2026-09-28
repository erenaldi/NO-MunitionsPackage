from cadgen import step
from study_shapes import build_study

@step(out="../STEP/C_Shoulder.step")
def study_c():
    return build_study("C")

if __name__ == "__main__":
    study_c()
