from cadgen import step

from halberd_r16_shapes import FOCUS_MATERIALS, build_r16, focus


@step(out="../STEP/halberd_r16_focus.step", materials=FOCUS_MATERIALS)
def halberd_r16_focus():
    return focus(build_r16())


if __name__ == "__main__":
    halberd_r16_focus()
