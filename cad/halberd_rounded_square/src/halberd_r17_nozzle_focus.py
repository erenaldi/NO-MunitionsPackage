from cadgen import declare_input, step

from halberd_r17_shapes import (
    BASELINE_STEP,
    NOZZLE_FOCUS_MATERIALS,
    build_r17_nozzle_focus,
)


@step(out="../STEP/halberd_r17_nozzle_focus.step", materials=NOZZLE_FOCUS_MATERIALS)
def halberd_r17_nozzle_focus():
    declare_input(BASELINE_STEP)
    return build_r17_nozzle_focus()


if __name__ == "__main__":
    halberd_r17_nozzle_focus()
