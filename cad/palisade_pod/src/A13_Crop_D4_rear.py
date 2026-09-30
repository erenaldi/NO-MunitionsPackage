from cadgen import step
from mounts import crop


@step(out="../STEP/A13_Crop_D4_rear.step")
def a13_crop_d3_rear():
    return crop("D4", "rear")


if __name__ == "__main__":
    a13_crop_d3_rear()
