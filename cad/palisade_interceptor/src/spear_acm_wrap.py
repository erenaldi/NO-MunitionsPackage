"""Uniform Spear with circumferential recessed ACM port pattern."""
from cadgen import step
from spear_acm_wrap_shapes import make_full_acm_pattern

@step(out="../STEP/Spear_ACMWrap.step")
def spear_acm_wrap():
    return make_full_acm_pattern()

if __name__ == "__main__":
    spear_acm_wrap()
