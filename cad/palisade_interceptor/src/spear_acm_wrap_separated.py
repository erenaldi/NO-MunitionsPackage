"""Cap with distributed ACM ports translated from unchanged main missile."""
from cadgen import step
from spear_acm_wrap_shapes import make_full_acm_pattern

@step(out="../STEP/Spear_ACMWrap_Separated.step")
def spear_acm_wrap_separated():
    return make_full_acm_pattern(separated=True)

if __name__ == "__main__":
    spear_acm_wrap_separated()
