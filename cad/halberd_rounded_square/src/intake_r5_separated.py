from cadgen import step
from intake_r5_shapes import build_r5

@step(out="../STEP/Selected_Intake_R5_Separated.step")
def intake_r5_separated():
    return build_r5(separated=True)

if __name__=="__main__":
    intake_r5_separated()
