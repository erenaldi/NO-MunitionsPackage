from cadgen import step
from variants import study


@step(out="../STEP/C_SlottedShell_Filled.step")
def c_slotted_shell_filled():
    return study("C", True)


if __name__ == "__main__":
    c_slotted_shell_filled()
