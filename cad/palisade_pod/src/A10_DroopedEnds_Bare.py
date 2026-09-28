from cadgen import step
from drooped_ends import study


@step(out="../STEP/A10_DroopedEnds_Bare.step")
def a10_drooped_ends_bare():
    return study(False)


if __name__ == "__main__":
    a10_drooped_ends_bare()
