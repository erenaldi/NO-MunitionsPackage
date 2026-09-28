from cadgen import step
from sketched_ends import study


@step(out="../STEP/A6_SketchedEnds_Bare.step")
def a6_sketched_ends_bare():
    return study(False)


if __name__ == "__main__":
    a6_sketched_ends_bare()
