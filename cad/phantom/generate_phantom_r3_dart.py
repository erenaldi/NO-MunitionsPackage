"""Build the RDM-9 Phantom R3 Dart of record: dorsal pop-out wings, no side emitters."""

from cadgen import report, step

from phantom_r2_lib import make_r2, make_r2_context


@step(out="RDM-9_Phantom_R3_Dart.step")
def phantom_r3_dart():
    report("R3 Dart: clean body, four tail fins, deployed dorsal pop-out wings")
    return make_r2("dart3")


@step(out="RDM-9_Phantom_R3_Context_Dart.step")
def phantom_r3_context_dart():
    report("R3 Dart with dorsal pylon-pad mockup")
    return make_r2_context("dart3")


if __name__ == "__main__":
    phantom_r3_dart()
    phantom_r3_context_dart()
