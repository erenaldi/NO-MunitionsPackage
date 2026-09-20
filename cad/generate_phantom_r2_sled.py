"""Build the RDM-9 Phantom round-2 candidate A: stowed-panel sled."""

from cadgen import report, step

from phantom_r2_lib import make_r2


@step(out="RDM-9_Phantom_R2_Sled.step")
def phantom_r2_sled():
    report("candidate A: long stowed-panel wings, low dorsal spine")
    return make_r2("sled")


if __name__ == "__main__":
    phantom_r2_sled()
