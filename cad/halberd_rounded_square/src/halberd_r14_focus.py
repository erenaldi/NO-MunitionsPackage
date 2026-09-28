from cadgen import step
from halberd_r14 import halberd_r14
from halberd_r14_shapes import booster_focus

@step(out="../STEP/halberd_r14_focus.step")
def halberd_r14_focus():
    return booster_focus(halberd_r14(), ("booster_fin_fairing_1",),
                         "Halberd_R14_Booster_Junction_Focus")

if __name__=="__main__":
    halberd_r14_focus()