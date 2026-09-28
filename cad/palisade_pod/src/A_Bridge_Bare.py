"""Palisade A / bridge-and-rails, with the four module bays visible."""
from cadgen import step
from housing import make_study


@step(out="../STEP/A_Bridge_Bare.step")
def a_bridge_bare():
    return make_study(False)


if __name__ == "__main__":
    a_bridge_bare()
