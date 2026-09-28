from cadgen import step
from intake_r3_shapes import build_r3

@step(out="../STEP/Selected_Intake_R3.step")
def intake_r3():
    return build_r3()

if __name__=="__main__":
    intake_r3()
