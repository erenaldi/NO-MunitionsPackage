"""Isolated cap with one stepped recessed nozzle and three reference stubs."""
from cadgen import step
from spear_banded_cap_shapes import make_banded_cap_preview

@step(out="../STEP/Spear_BandedCap_Cap_Focus.step")
def spear_banded_cap_focus():
    return make_banded_cap_preview(cap_only=True)

if __name__ == "__main__":
    spear_banded_cap_focus()
