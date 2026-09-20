"""Build the RDM-9 Phantom round-2 candidate C: four-fin tail dart."""

from cadgen import report, step

from phantom_r2_lib import make_r2


@step(out="RDM-9_Phantom_R2_Dart.step")
def phantom_r2_dart():
    report("candidate C: clean body, four real-span tail fins")
    return make_r2("dart")


if __name__ == "__main__":
    phantom_r2_dart()
