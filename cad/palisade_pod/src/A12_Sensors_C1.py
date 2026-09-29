from cadgen import step
from sensors import study


@step(out="../STEP/A12_Sensors_C1.step")
def a12_sensors_c1():
    return study(1)


if __name__ == "__main__":
    a12_sensors_c1()
