from cadgen import step

from halberd_r16_shapes import MATERIALS, build_r16


@step(out="../STEP/halberd_r16.step", materials=MATERIALS)
def halberd_r16():
    return build_r16()


if __name__ == "__main__":
    halberd_r16()
