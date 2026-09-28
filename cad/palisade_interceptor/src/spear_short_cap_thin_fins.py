"""Selected Spear study with 130 mm cap and slightly thinner four-fin set."""
from cadgen import step
from spear_short_cap_shapes import make_short_cap

@step(out="../STEP/Spear_ShortCap_ThinFins.step")
def spear_short_cap_thin_fins():
    return make_short_cap()

if __name__ == "__main__":
    spear_short_cap_thin_fins()
