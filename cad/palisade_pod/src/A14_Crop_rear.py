from cadgen import step
from rear_window import crop_rear


@step(out="../STEP/A14_Crop_rear.step")
def a14_crop_rear():
    return crop_rear()


if __name__ == "__main__":
    a14_crop_rear()
