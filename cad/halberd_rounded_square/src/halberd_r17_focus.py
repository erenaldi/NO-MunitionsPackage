from cadgen import declare_input, step

from halberd_r17_shapes import (
    BASELINE_STEP,
    BODY_FOCUS_MATERIALS,
    build_r17_body_focus,
)


@step(out="../STEP/halberd_r17_focus.step", materials=BODY_FOCUS_MATERIALS)
def halberd_r17_focus():
    declare_input(BASELINE_STEP)
    return build_r17_body_focus()


if __name__ == "__main__":
    halberd_r17_focus()
