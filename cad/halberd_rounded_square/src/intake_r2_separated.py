from cadgen import step
from intake_r2_shapes import build_r2

@step(out="../STEP/Selected_Intake_R2_Separated.step")
def intake_r2_separated():
    return build_r2(separated=True)

if __name__=="__main__":
    intake_r2_separated()
