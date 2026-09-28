from cadgen import step
from rounded_tips import study


@step(out="../STEP/A8_RoundedTips_Filled.step")
def a8_rounded_tips_filled():
    return study(True)


if __name__ == "__main__":
    a8_rounded_tips_filled()
