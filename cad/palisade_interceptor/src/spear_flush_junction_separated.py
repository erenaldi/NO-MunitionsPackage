"""Selected Spear with flush seam and translated cap for stage review."""
from cadgen import step
from spear_flush_junction_shapes import make_flush_junction

@step(out="../STEP/Spear_FlushJunction_Cap_Separated.step")
def spear_flush_junction_separated():
    return make_flush_junction(separated=True)

if __name__ == "__main__":
    spear_flush_junction_separated()
