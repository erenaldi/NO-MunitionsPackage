from cadgen import step
from halberd_r10 import halberd_r10
from halberd_r10_shapes import focus

@step(out="../STEP/halberd_r10_focus.step")
def halberd_r10_focus():
    return focus(halberd_r10())

if __name__=="__main__":
    halberd_r10_focus()
