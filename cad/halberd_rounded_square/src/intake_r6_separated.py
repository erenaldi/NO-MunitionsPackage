from cadgen import step
from intake_r6_shapes import build_r6

@step(out="../STEP/Selected_Intake_R6_Separated.step")
def intake_r6_separated():
    return build_r6(separated=True)

if __name__=="__main__":
    intake_r6_separated()
