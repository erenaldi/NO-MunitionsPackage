from cadgen import declare_input, step

from halberd_r17_shapes import BASELINE_STEP, MATERIALS, build_r17_separated


@step(out="../STEP/halberd_r17_separated.step", materials=MATERIALS)
def halberd_r17_separated():
    declare_input(BASELINE_STEP)
    return build_r17_separated()


if __name__ == "__main__":
    halberd_r17_separated()
