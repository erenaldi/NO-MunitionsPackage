from cadgen import step
from sensors import crop


@step(out="../STEP/A12_Crop_C6_rear.step")
def a12_crop_c1_rear():
    return crop(6, "rear")


if __name__ == "__main__":
    a12_crop_c1_rear()
