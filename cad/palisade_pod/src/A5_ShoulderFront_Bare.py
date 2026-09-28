from cadgen import step
from mount_front_shoulder import study


@step(out="../STEP/A5_ShoulderFront_Bare.step")
def a5_shoulder_front_bare():
    return study(False)


if __name__ == "__main__":
    a5_shoulder_front_bare()
