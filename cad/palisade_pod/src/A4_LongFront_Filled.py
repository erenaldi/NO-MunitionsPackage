from cadgen import step
from mount_front_long import study


@step(out="../STEP/A4_LongFront_Filled.step")
def a4_long_front_filled():
    return study(True)


if __name__ == "__main__":
    a4_long_front_filled()
