"""Detached cap view of the reference-led band/nozzle prototype."""
from cadgen import step
from spear_banded_cap_shapes import make_banded_cap_preview

@step(out="../STEP/Spear_BandedCap_Nozzle0_Separated.step")
def spear_banded_cap_nozzle0_separated():
    return make_banded_cap_preview(separated=True)

if __name__ == "__main__":
    spear_banded_cap_nozzle0_separated()
