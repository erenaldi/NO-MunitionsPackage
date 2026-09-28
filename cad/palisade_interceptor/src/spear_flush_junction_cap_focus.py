"""Isolated full-radius aft-filleted cap and one detailed nozzle."""
from cadgen import step
from spear_flush_junction_shapes import make_flush_junction

@step(out="../STEP/Spear_FlushJunction_Cap_Focus.step")
def spear_flush_junction_cap_focus():
    return make_flush_junction(cap_only=True)

if __name__ == "__main__":
    spear_flush_junction_cap_focus()
