"""Build pylon-context variants of the round-2 Phantom candidates."""

from cadgen import report, step

from phantom_r2_lib import make_r2_context


@step(out="RDM-9_Phantom_R2_Context_Sled.step")
def phantom_r2_context_sled():
    report("candidate A with dorsal pylon-pad mockup")
    return make_r2_context("sled")


@step(out="RDM-9_Phantom_R2_Context_Rails.step")
def phantom_r2_context_rails():
    report("candidate B with dorsal pylon-pad mockup")
    return make_r2_context("rails")


@step(out="RDM-9_Phantom_R2_Context_Dart.step")
def phantom_r2_context_dart():
    report("candidate C with dorsal pylon-pad mockup")
    return make_r2_context("dart")


if __name__ == "__main__":
    phantom_r2_context_sled()
    phantom_r2_context_rails()
    phantom_r2_context_dart()
