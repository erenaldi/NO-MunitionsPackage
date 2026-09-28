"""Plain Spear cap with a genuinely flush full-radius body seam."""
from cadgen import step
from spear_flush_junction_shapes import make_flush_junction

@step(out="../STEP/Spear_FlushJunction_Cap.step")
def spear_flush_junction():
    return make_flush_junction()

if __name__ == "__main__":
    spear_flush_junction()
