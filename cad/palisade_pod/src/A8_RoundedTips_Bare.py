from cadgen import step
from rounded_tips import study


@step(out="../STEP/A8_RoundedTips_Bare.step")
def a8_rounded_tips_bare():
    return study(False)


if __name__ == "__main__":
    a8_rounded_tips_bare()
