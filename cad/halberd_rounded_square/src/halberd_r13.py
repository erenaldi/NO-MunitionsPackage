from cadgen import step
from halberd_r12 import halberd_r12
from halberd_r13_shapes import detail, MATERIALS

@step(out="../STEP/halberd_r13.step",materials=MATERIALS)
def halberd_r13():
    return detail(halberd_r12())

if __name__=="__main__":
    halberd_r13()
