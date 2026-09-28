from cadgen import declare_input, step

from halberd_r17_shapes import (
    BASELINE_STEP,
    BOOSTER_FIN_FOCUS_MATERIALS,
    build_r17_booster_fin_focus,
)


@step(out="../STEP/halberd_r17_booster_fin_focus.step",
      materials=BOOSTER_FIN_FOCUS_MATERIALS)
def halberd_r17_booster_fin_focus():
    declare_input(BASELINE_STEP)
    return build_r17_booster_fin_focus()


if __name__ == "__main__":
    halberd_r17_booster_fin_focus()
