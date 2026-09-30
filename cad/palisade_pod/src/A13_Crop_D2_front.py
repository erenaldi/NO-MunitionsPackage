from cadgen import step
from mounts import crop


@step(out="../STEP/A13_Crop_D2_front.step")
def a13_crop_d2_front():
    return crop("D2", "front")


if __name__ == "__main__":
    a13_crop_d2_front()
