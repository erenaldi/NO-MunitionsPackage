from cadgen import step
from variants import study


@step(out="../STEP/B_OpenCrown_Filled.step")
def b_open_crown_filled():
    return study("B", True)


if __name__ == "__main__":
    b_open_crown_filled()
