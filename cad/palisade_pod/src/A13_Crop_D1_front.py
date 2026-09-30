from cadgen import step
from mounts import crop


@step(out="../STEP/A13_Crop_D1_front.step")
def a13_crop_d1_front():
    return crop("D1", "front")


if __name__ == "__main__":
    a13_crop_d1_front()
