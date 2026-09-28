from cadgen import step
from intake_r2_shapes import build_r2

@step(out="../STEP/Selected_Intake_R2.step")
def intake_r2():
    return build_r2()

if __name__=="__main__":
    intake_r2()
