from cadgen import step
from sensors import study


@step(out="../STEP/A12_Sensors_C6.step")
def a12_sensors_c3():
    return study(6)


if __name__ == "__main__":
    a12_sensors_c3()
