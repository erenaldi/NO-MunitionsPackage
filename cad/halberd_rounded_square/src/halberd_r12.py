from cadgen import step
from halberd_r12_shapes import build_r12, MATERIALS

@step(out="../STEP/halberd_r12.step",materials=MATERIALS)
def halberd_r12():
    return build_r12()

if __name__=="__main__":
    halberd_r12()
