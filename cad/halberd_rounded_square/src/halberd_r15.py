from cadgen import step
from halberd_r15_shapes import build_r15, MATERIALS

@step(out="../STEP/halberd_r15.step",materials=MATERIALS)
def halberd_r15():
    return build_r15()

if __name__=="__main__":
    halberd_r15()