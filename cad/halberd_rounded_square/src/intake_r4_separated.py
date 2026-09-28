from cadgen import step
from intake_r4_shapes import build_r4

@step(out="../STEP/Selected_Intake_R4_Separated.step")
def intake_r4_separated():
    return build_r4(separated=True)

if __name__=="__main__":
    intake_r4_separated()
