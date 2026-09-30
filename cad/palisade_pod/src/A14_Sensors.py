from cadgen import step
from rear_window import study


@step(out="../STEP/A14_Sensors.step")
def a14_sensors():
    return study()


if __name__ == "__main__":
    a14_sensors()
