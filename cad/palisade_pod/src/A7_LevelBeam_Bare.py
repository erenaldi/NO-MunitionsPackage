from cadgen import step
from sketch_refine import study


@step(out="../STEP/A7_LevelBeam_Bare.step")
def a7_level_beam_bare():
    return study(False)


if __name__ == "__main__":
    a7_level_beam_bare()
