from cadgen import step
from halberd_r9_shapes import build_r9, MATERIALS

@step(out="../STEP/halberd_r9_separated.step",materials=MATERIALS)
def halberd_r9_separated():
    return build_r9(separated=True)

if __name__=="__main__":
    halberd_r9_separated()
