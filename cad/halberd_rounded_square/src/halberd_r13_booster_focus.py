"""Saved R13 baseline at the booster junction for matched before/after views."""
from cadgen import step
from halberd_r13 import halberd_r13
from halberd_r14_shapes import booster_focus

@step(out="../STEP/halberd_r13_booster_focus.step")
def halberd_r13_booster_focus():
    return booster_focus(halberd_r13(), ("booster_fin_1", "booster_intake_fairing_1"),
                         "Halberd_R13_Booster_Junction_Focus")

if __name__=="__main__":
    halberd_r13_booster_focus()