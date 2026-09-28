from cadgen import step
from halberd_r15_shapes import build_r15, focus, FOCUS_MATERIALS

@step(out="../STEP/halberd_r15_focus.step",materials=FOCUS_MATERIALS)
def halberd_r15_focus():
    return focus(build_r15())

if __name__=="__main__":
    halberd_r15_focus()