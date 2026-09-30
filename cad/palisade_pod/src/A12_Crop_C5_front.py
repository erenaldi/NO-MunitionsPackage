from cadgen import step
from sensors import crop


@step(out="../STEP/A12_Crop_C5_front.step")
def a12_crop_c1_front():
    return crop(5, "front")


if __name__ == "__main__":
    a12_crop_c1_front()
