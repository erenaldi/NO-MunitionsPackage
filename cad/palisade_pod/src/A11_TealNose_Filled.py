from cadgen import step
from teal_nose import study


@step(out="../STEP/A11_TealNose_Filled.step")
def a11_teal_nose_filled():
    return study(True)


if __name__ == "__main__":
    a11_teal_nose_filled()
