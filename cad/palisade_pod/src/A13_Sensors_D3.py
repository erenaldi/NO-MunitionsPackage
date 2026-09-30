from cadgen import step
from mounts import study


@step(out="../STEP/A13_Sensors_D3.step")
def a13_sensors_d3():
    return study("D3")


if __name__ == "__main__":
    a13_sensors_d3()
