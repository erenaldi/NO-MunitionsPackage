"""Isolated cap for aft-taper and four-thruster review."""
from cadgen import step
from spear_revision_shapes import make_cap_focus

@step(out="../STEP/Spear_Boattail_Cap_Focus.step")
def spear_boattail_cap_focus():
    return make_cap_focus()

if __name__ == "__main__":
    spear_boattail_cap_focus()
