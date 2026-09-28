from cadgen import step
from halberd_r10_shapes import build_r10, MATERIALS

@step(out="../STEP/halberd_r10.step",materials=MATERIALS)
def halberd_r10():
    return build_r10()

if __name__=="__main__":
    halberd_r10()
