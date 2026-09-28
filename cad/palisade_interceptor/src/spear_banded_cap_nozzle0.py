"""Selected Spear with reference-led band and one detailed cap nozzle."""
from cadgen import step
from spear_banded_cap_shapes import make_banded_cap_preview

@step(out="../STEP/Spear_BandedCap_Nozzle0.step")
def spear_banded_cap_nozzle0():
    return make_banded_cap_preview()

if __name__ == "__main__":
    spear_banded_cap_nozzle0()
