from cadgen import step
from study_shapes import build_study

@step(out="../STEP/C_Shoulder_Separated.step")
def study_c_separated():
    return build_study("C", separated=True)

if __name__ == "__main__":
    study_c_separated()
