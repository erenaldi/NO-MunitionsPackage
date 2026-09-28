"""Build the RDM-9 Phantom R5 configurations: thinned deployed wings + retracted bay."""

from cadgen import report, step

from phantom_r2_lib import make_r2, make_r2_context


@step(out="RDM-9_Phantom_R5_Dart.step")
def phantom_r5_dart():
    report("R5 dart5 deployed: 2.5 mm folding panels swept out")
    return make_r2("dart5")


@step(out="RDM-9_Phantom_R5_Dart_Retracted.step")
def phantom_r5_dart_retracted():
    report("R5 dart5r retracted: panels parked in the dorsal bay")
    return make_r2("dart5r")


@step(out="RDM-9_Phantom_R5_Context_Dart_Retracted.step")
def phantom_r5_context_dart_retracted():
    report("R5 dart5r retracted with dorsal pylon-pad mockup")
    return make_r2_context("dart5r")


if __name__ == "__main__":
    phantom_r5_dart()
    phantom_r5_dart_retracted()
    phantom_r5_context_dart_retracted()
