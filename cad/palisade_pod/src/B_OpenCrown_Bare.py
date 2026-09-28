from cadgen import step
from variants import study


@step(out="../STEP/B_OpenCrown_Bare.step")
def b_open_crown_bare():
    return study("B", False)


if __name__ == "__main__":
    b_open_crown_bare()
