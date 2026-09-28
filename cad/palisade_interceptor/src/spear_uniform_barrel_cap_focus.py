"""Isolated small-diameter cap with one detailed lateral-nozzle prototype."""
from cadgen import step
from spear_uniform_barrel_shapes import make_uniform_spear

@step(out="../STEP/Spear_UniformBarrel_Cap_Focus.step")
def spear_uniform_barrel_cap_focus():
    return make_uniform_spear(cap_only=True)

if __name__ == "__main__":
    spear_uniform_barrel_cap_focus()
