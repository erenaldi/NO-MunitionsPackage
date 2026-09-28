from cadgen import step
from halberd_r11_shapes import build_r11, MATERIALS

@step(out="../STEP/halberd_r11_separated.step",materials=MATERIALS)
def halberd_r11_separated():
    return build_r11(separated=True)

if __name__=="__main__":
    halberd_r11_separated()
