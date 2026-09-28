from cadgen import step
from variants import study


@step(out="../STEP/C_SlottedShell_Bare.step")
def c_slotted_shell_bare():
    return study("C", False)


if __name__ == "__main__":
    c_slotted_shell_bare()
