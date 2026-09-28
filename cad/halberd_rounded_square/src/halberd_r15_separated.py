from cadgen import step
from halberd_r15_shapes import build_r15, MATERIALS

@step(out="../STEP/halberd_r15_separated.step",materials=MATERIALS)
def halberd_r15_separated():
    return build_r15(separated=True)

if __name__=="__main__":
    halberd_r15_separated()