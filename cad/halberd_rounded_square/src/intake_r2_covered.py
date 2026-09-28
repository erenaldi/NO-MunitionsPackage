from cadgen import step
from intake_r2_shapes import build_r2

@step(out="../STEP/Selected_Intake_R2_Covered.step")
def intake_r2_covered():
    return build_r2(covered=True)

if __name__=="__main__":
    intake_r2_covered()
