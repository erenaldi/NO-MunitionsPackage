from cadgen import step
from sensors import study


@step(out="../STEP/A12_Sensors_C2.step")
def a12_sensors_c2():
    return study(2)


if __name__ == "__main__":
    a12_sensors_c2()
