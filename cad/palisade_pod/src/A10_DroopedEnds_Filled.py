from cadgen import step
from drooped_ends import study


@step(out="../STEP/A10_DroopedEnds_Filled.step")
def a10_drooped_ends_filled():
    return study(True)


if __name__ == "__main__":
    a10_drooped_ends_filled()
