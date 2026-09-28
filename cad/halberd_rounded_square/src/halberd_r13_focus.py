from cadgen import step
from halberd_r13 import halberd_r13
from halberd_r13_shapes import focus, FOCUS_MATERIALS

@step(out="../STEP/halberd_r13_focus.step",materials=FOCUS_MATERIALS)
def halberd_r13_focus():
    return focus(halberd_r13())

if __name__=="__main__":
    halberd_r13_focus()
