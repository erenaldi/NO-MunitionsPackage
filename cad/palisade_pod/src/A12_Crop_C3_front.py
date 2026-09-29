from cadgen import step
from sensors import crop


@step(out="../STEP/A12_Crop_C3_front.step")
def a12_crop_c3_front():
    return crop(3, "front")


if __name__ == "__main__":
    a12_crop_c3_front()
