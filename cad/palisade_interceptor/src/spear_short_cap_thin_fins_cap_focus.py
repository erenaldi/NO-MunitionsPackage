"""Isolated shortened cap with one stepped lateral-nozzle prototype."""
from cadgen import step
from spear_short_cap_shapes import make_short_cap

@step(out="../STEP/Spear_ShortCap_ThinFins_Cap_Focus.step")
def spear_short_cap_thin_fins_cap_focus():
    return make_short_cap(cap_only=True)

if __name__ == "__main__":
    spear_short_cap_thin_fins_cap_focus()
