from cadgen import step
from sensors import study


@step(out="../STEP/A12_Sensors_C4.step")
def a12_sensors_c3():
    return study(4)


if __name__ == "__main__":
    a12_sensors_c3()
