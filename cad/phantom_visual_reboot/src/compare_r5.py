"""True-scale four-up CAD comparison, labeled by per-part source identifiers.

All parts are rigidly translated without resizing. Display is read-only;
these STEP outputs are review assemblies, not new release masters.
"""

from pathlib import Path
from cadgen import build123d as bd, read_step, step


ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT.parent
NAMES = {"A": "Facet", "B": "Shoulder", "C": "Keel"}
STATIONS = [("R5", -1550., 1150.), ("A", 1550., 1150.),
            ("B", -1550., -1150.), ("C", 1550., -1150.)]


def arrangement(pose):
    outputs = []
    for key, x, y in STATIONS:
        if key == "R5":
            name = "RDM-9_Phantom_R5_Dart" + ("_Retracted" if pose == "stowed" else "") + ".step"
            model = read_step(CAD / name)
        else:
            model = read_step(ROOT / "STEP" / ("%s_%s_%s.step" % (key, NAMES[key], pose.title())))
        for part in model.children:
            positioned = part.moved(bd.Location((x, y, 0)))
            positioned.label = key + "_" + part.label
            outputs.append(positioned)
    return bd.Compound(children=outputs, label="RDM9_R5_ABC_%s_TrueScale" % pose)


@step(out="../STEP/R5_ABC_Deployed_TrueScale.step")
def deployed():
    return arrangement("deployed")


@step(out="../STEP/R5_ABC_Stowed_TrueScale.step")
def stowed():
    return arrangement("stowed")


if __name__ == "__main__":
    deployed()
    stowed()
