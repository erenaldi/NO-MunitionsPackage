"""Review-only detached rounded turning cap on the unchanged selected Spear."""
from cadgen import step
from spear_revision_shapes import make_rounded_cap_preview

@step(out="../STEP/Spear_RoundedTip_Boattail_Separated.step")
def spear_rounded_tip_separated():
    return make_rounded_cap_preview(separated=True)

if __name__ == "__main__":
    spear_rounded_tip_separated()
