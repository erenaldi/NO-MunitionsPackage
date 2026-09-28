from cadgen import step
from continuous_ends import study


@step(out="../STEP/A9_ContinuousEnds_Bare.step")
def a9_continuous_ends_bare():
    return study(False)


if __name__ == "__main__":
    a9_continuous_ends_bare()
