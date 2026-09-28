"""Build the RDM-9 Phantom R6 configurations: slender fold-compatible wings + tucked retracted state."""

from cadgen import report, step

from phantom_r2_lib import make_r2, make_r2_context


@step(out="RDM-9_Phantom_R6_Dart.step")
def phantom_r6_dart():
    report("R6 dart6 deployed: slender fold-compatible swept wings")
    return make_r2("dart6")


@step(out="RDM-9_Phantom_R6_Dart_Retracted.step")
def phantom_r6_dart_retracted():
    report("R6 dart6r retracted: panels tucked flat against the upper flanks")
    return make_r2("dart6r")


@step(out="RDM-9_Phantom_R6_Context_Dart_Retracted.step")
def phantom_r6_context_dart_retracted():
    report("R6 dart6r retracted with dorsal pylon-pad mockup")
    return make_r2_context("dart6r")


if __name__ == "__main__":
    phantom_r6_dart()
    phantom_r6_dart_retracted()
    phantom_r6_context_dart_retracted()
