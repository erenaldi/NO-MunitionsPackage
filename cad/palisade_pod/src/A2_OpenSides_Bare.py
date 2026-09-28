"""Selected-A direction, modified for bare exposed side seats."""
from cadgen import step
from housing import make_open_side_study


@step(out="../STEP/A2_OpenSides_Bare.step")
def a2_open_sides_bare():
    return make_open_side_study(False)


if __name__ == "__main__":
    a2_open_sides_bare()
