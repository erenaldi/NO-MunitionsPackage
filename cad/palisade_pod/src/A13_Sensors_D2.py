from cadgen import step
from mounts import study


@step(out="../STEP/A13_Sensors_D2.step")
def a13_sensors_d2():
    return study("D2")


if __name__ == "__main__":
    a13_sensors_d2()
