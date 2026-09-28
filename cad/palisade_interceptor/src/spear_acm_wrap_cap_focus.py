"""Isolated cap showing all around-the-cylinder ACM blind ports."""
from cadgen import step
from spear_acm_wrap_shapes import make_full_acm_pattern

@step(out="../STEP/Spear_ACMWrap_Cap_Focus.step")
def spear_acm_wrap_cap_focus():
    return make_full_acm_pattern(cap_only=True)

if __name__ == "__main__":
    spear_acm_wrap_cap_focus()
