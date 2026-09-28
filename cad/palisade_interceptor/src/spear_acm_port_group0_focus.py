"""Cap-only study of six inset openings and three unmodified motor groups."""
from cadgen import step
from spear_acm_port_shapes import make_acm_group_preview

@step(out="../STEP/Spear_ACMPortGroup0_Cap_Focus.step")
def spear_acm_port_group0_focus():
    return make_acm_group_preview(cap_only=True)

if __name__ == "__main__":
    spear_acm_port_group0_focus()
