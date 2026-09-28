"""Separated short cap, main nozzle exposed, main body still 1,200 mm long."""
from cadgen import step
from spear_short_cap_shapes import make_short_cap

@step(out="../STEP/Spear_ShortCap_ThinFins_Separated.step")
def spear_short_cap_thin_fins_separated():
    return make_short_cap(separated=True)

if __name__ == "__main__":
    spear_short_cap_thin_fins_separated()
