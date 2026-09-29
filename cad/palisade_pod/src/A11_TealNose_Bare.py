from cadgen import step
from teal_nose import study


@step(out="../STEP/A11_TealNose_Bare.step")
def a11_teal_nose_bare():
    return study(False)


if __name__ == "__main__":
    a11_teal_nose_bare()
