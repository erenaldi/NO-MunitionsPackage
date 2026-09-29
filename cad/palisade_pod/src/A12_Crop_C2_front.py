from cadgen import step
from sensors import crop


@step(out="../STEP/A12_Crop_C2_front.step")
def a12_crop_c2_front():
    return crop(2, "front")


if __name__ == "__main__":
    a12_crop_c2_front()
