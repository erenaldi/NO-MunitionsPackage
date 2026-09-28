from cadgen import step
from halberd_r14_shapes import build_r14, MATERIALS

@step(out="../STEP/halberd_r14.step",materials=MATERIALS)
def halberd_r14():
    return build_r14()

if __name__=="__main__":
    halberd_r14()