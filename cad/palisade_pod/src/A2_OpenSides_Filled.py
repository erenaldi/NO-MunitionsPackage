"""Selected-A direction with four placeholders making the visible sides."""
from cadgen import step
from housing import make_open_side_study


@step(out="../STEP/A2_OpenSides_Filled.step")
def a2_open_sides_filled():
    return make_open_side_study(True)


if __name__ == "__main__":
    a2_open_sides_filled()
