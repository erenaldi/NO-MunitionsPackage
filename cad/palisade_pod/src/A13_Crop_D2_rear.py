from cadgen import step
from mounts import crop


@step(out="../STEP/A13_Crop_D2_rear.step")
def a13_crop_d2_rear():
    return crop("D2", "rear")


if __name__ == "__main__":
    a13_crop_d2_rear()
