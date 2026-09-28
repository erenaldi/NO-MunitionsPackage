from cadgen import step
from sketch_refine import study


@step(out="../STEP/A7_LevelBeam_Filled.step")
def a7_level_beam_filled():
    return study(True)


if __name__ == "__main__":
    a7_level_beam_filled()
