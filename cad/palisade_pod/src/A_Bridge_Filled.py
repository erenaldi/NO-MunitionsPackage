"""Palisade A / bridge-and-rails, four simple flush cassette placeholders."""
from cadgen import step
from housing import make_study


@step(out="../STEP/A_Bridge_Filled.step")
def a_bridge_filled():
    return make_study(True)


if __name__ == "__main__":
    a_bridge_filled()
