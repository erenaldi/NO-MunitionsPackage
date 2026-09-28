from cadgen import step
from intake_r5_shapes import build_r5

@step(out="../STEP/Selected_Intake_R5.step")
def intake_r5():
    return build_r5()

if __name__=="__main__":
    intake_r5()
