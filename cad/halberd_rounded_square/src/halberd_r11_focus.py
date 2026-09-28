from cadgen import step
from halberd_r11 import halberd_r11
from halberd_r11_shapes import focus

@step(out="../STEP/halberd_r11_focus.step")
def halberd_r11_focus():
    model=focus(halberd_r11())
    model.label="Halberd_R11_Ridge_Aligned_Focus"
    return model

if __name__=="__main__":
    halberd_r11_focus()
