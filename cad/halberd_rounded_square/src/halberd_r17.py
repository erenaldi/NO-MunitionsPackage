from cadgen import step
try:
    from cadgen import declare_input
except ImportError:  # cadgen >= 0.7.10 traces input reads itself
    def declare_input(_path):
        return None

from halberd_r17_shapes import BASELINE_STEP, MATERIALS, build_r17


@step(out="../STEP/halberd_r17.step", materials=MATERIALS)
def halberd_r17():
    declare_input(BASELINE_STEP)
    return build_r17()


if __name__ == "__main__":
    halberd_r17()
