from cadgen import step
from mount_front import study


@step(out="../STEP/A3_MountFront_Filled.step")
def a3_mount_front_filled():
    return study(True)


if __name__ == "__main__":
    a3_mount_front_filled()
