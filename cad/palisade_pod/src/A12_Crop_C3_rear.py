from cadgen import step
from sensors import crop


@step(out="../STEP/A12_Crop_C3_rear.step")
def a12_crop_c3_rear():
    return crop(3, "rear")


if __name__ == "__main__":
    a12_crop_c3_rear()
