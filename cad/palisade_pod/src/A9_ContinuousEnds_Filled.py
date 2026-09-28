from cadgen import step
from continuous_ends import study


@step(out="../STEP/A9_ContinuousEnds_Filled.step")
def a9_continuous_ends_filled():
    return study(True)


if __name__ == "__main__":
    a9_continuous_ends_filled()
