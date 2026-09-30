from cadgen import step
from mounts import study


@step(out="../STEP/A13_Sensors_D1.step")
def a13_sensors_d1():
    return study("D1")


if __name__ == "__main__":
    a13_sensors_d1()
