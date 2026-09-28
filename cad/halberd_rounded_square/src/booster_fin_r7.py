from cadgen import step
from booster_fin_r7_shapes import build_r7

@step(out="../STEP/Selected_Halberd_R7.step")
def booster_fin_r7():
    return build_r7()

if __name__=="__main__":
    booster_fin_r7()
