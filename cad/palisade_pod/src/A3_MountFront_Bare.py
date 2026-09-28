from cadgen import step
from mount_front import study


@step(out="../STEP/A3_MountFront_Bare.step")
def a3_mount_front_bare():
    return study(False)


if __name__ == "__main__":
    a3_mount_front_bare()
