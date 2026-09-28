"""Uniform Spear with only one PAC-3-inspired inset ACM port group."""
from cadgen import step
from spear_acm_port_shapes import make_acm_group_preview

@step(out="../STEP/Spear_ACMPortGroup0.step")
def spear_acm_port_group0():
    return make_acm_group_preview()

if __name__ == "__main__":
    spear_acm_port_group0()
