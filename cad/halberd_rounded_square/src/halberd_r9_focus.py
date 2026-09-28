from cadgen import step
from halberd_r9 import halberd_r9
from halberd_r9_shapes import focus

@step(out="../STEP/halberd_r9_focus.step")
def halberd_r9_focus():
    return focus(halberd_r9())

if __name__=="__main__":
    halberd_r9_focus()
