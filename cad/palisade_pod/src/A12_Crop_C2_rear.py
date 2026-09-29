from cadgen import step
from sensors import crop


@step(out="../STEP/A12_Crop_C2_rear.step")
def a12_crop_c2_rear():
    return crop(2, "rear")


if __name__ == "__main__":
    a12_crop_c2_rear()
