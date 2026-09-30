from cadgen import step
from mounts import crop


@step(out="../STEP/A13_Crop_D4_front.step")
def a13_crop_d3_front():
    return crop("D4", "front")


if __name__ == "__main__":
    a13_crop_d3_front()
