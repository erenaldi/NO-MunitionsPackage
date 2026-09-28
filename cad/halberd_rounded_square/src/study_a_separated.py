from cadgen import step
from study_shapes import build_study

@step(out="../STEP/A_Trace_Separated.step")
def study_a_separated():
    return build_study("A", separated=True)

if __name__ == "__main__":
    study_a_separated()
