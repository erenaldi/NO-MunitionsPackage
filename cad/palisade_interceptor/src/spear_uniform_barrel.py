"""One-diameter Spear missile and cap with 130 mm detachable tail."""
from cadgen import step
from spear_uniform_barrel_shapes import make_uniform_spear

@step(out="../STEP/Spear_UniformBarrel.step")
def spear_uniform_barrel():
    return make_uniform_spear()

if __name__ == "__main__":
    spear_uniform_barrel()
