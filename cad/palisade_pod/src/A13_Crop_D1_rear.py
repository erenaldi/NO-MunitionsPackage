from cadgen import step
from mounts import crop


@step(out="../STEP/A13_Crop_D1_rear.step")
def a13_crop_d1_rear():
    return crop("D1", "rear")


if __name__ == "__main__":
    a13_crop_d1_rear()
