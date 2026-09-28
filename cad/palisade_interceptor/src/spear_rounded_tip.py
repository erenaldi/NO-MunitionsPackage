"""Four-fin Spear with revised round-ended turning-cap boattail."""
from cadgen import step
from spear_revision_shapes import make_rounded_cap_preview

@step(out="../STEP/Spear_RoundedTip_Boattail.step")
def spear_rounded_tip():
    return make_rounded_cap_preview()

if __name__ == "__main__":
    spear_rounded_tip()
