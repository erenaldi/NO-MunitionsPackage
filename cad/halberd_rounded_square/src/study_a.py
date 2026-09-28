from cadgen import step
from study_shapes import build_study

@step(out="../STEP/A_Trace.step")
def study_a():
    return build_study("A")

if __name__ == "__main__":
    study_a()
