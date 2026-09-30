from cadgen import step
from sensors import crop


@step(out="../STEP/A12_Crop_C4_rear.step")
def a12_crop_c1_rear():
    return crop(4, "rear")


if __name__ == "__main__":
    a12_crop_c1_rear()
