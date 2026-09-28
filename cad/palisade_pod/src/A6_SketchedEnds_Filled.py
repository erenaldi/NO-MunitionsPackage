from cadgen import step
from sketched_ends import study


@step(out="../STEP/A6_SketchedEnds_Filled.step")
def a6_sketched_ends_filled():
    return study(True)


if __name__ == "__main__":
    a6_sketched_ends_filled()
