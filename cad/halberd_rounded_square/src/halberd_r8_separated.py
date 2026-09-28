from cadgen import step
from halberd_r8_shapes import build_r8, MATERIALS

@step(out="../STEP/Selected_Halberd_R8_Separated.step",materials=MATERIALS)
def halberd_r8_separated():
    return build_r8(separated=True)

if __name__=="__main__":
    halberd_r8_separated()
