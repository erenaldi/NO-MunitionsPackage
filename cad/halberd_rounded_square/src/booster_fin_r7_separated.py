from cadgen import step
from booster_fin_r7_shapes import build_r7

@step(out="../STEP/Selected_Halberd_R7_Separated.step")
def booster_fin_r7_separated():
    return build_r7(separated=True)

if __name__=="__main__":
    booster_fin_r7_separated()
