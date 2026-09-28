from cadgen import step
from intake_r3_shapes import build_r3

@step(out="../STEP/Selected_Intake_R3_Separated.step")
def intake_r3_separated():
    return build_r3(separated=True)

if __name__=="__main__":
    intake_r3_separated()
