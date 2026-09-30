from cadgen import step
from mounts import crop


@step(out="../STEP/A13_Crop_D3_front.step")
def a13_crop_d3_front():
    return crop("D3", "front")


if __name__ == "__main__":
    a13_crop_d3_front()
