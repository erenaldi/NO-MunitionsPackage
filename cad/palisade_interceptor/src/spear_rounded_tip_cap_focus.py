"""Isolated rounded closed cap and four lateral thrusters."""
from cadgen import step
from spear_revision_shapes import make_rounded_cap_preview

@step(out="../STEP/Spear_RoundedTip_Cap_Focus.step")
def spear_rounded_tip_cap_focus():
    return make_rounded_cap_preview(cap_only=True)

if __name__ == "__main__":
    spear_rounded_tip_cap_focus()
