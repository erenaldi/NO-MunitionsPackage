"""Uniform Spear with the turning cap translated for review."""
from cadgen import step
from spear_uniform_barrel_shapes import make_uniform_spear

@step(out="../STEP/Spear_UniformBarrel_Separated.step")
def spear_uniform_barrel_separated():
    return make_uniform_spear(separated=True)

if __name__ == "__main__":
    spear_uniform_barrel_separated()
