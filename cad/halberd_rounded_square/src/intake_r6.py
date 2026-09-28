from cadgen import step
from intake_r6_shapes import build_r6

@step(out="../STEP/Selected_Intake_R6.step")
def intake_r6():
    return build_r6()

if __name__=="__main__":
    intake_r6()
