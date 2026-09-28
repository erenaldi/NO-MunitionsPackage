"""Separated cap review of one inset ACM port group."""
from cadgen import step
from spear_acm_port_shapes import make_acm_group_preview

@step(out="../STEP/Spear_ACMPortGroup0_Separated.step")
def spear_acm_port_group0_separated():
    return make_acm_group_preview(separated=True)

if __name__ == "__main__":
    spear_acm_port_group0_separated()
