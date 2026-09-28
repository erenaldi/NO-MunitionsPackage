"""Build the RDM-9 Phantom R4 dart4 of record: sharp apex nose, swept pop-out wings."""

from cadgen import report, step

from phantom_r2_lib import make_r2, make_r2_context


@step(out="RDM-9_Phantom_R4_Dart.step")
def phantom_r4_dart():
    report("R4 dart4: smooth wedge body to a sharp apex, swept pop-out wings")
    return make_r2("dart4")


@step(out="RDM-9_Phantom_R4_Context_Dart.step")
def phantom_r4_context_dart():
    report("R4 dart4 with dorsal pylon-pad mockup")
    return make_r2_context("dart4")


if __name__ == "__main__":
    phantom_r4_dart()
    phantom_r4_context_dart()
