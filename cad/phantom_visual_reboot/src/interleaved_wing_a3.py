"""A3 — A2 geometry lowered into a fixed, probe-passed body recess.

The original body is retained and cut only by the specified well and four
layer slots. Every nonbody A2 component receives the same -22.75 mm Z shift.
This is a source/build gate, not production approval.
"""
from cadgen import build123d as bd, step
from interleaved_wing_a2 import (
    LAYERS as A2_LAYERS,
    body as a2_body,
    box,
    components as a2_components,
    place_panel as a2_place_panel,
    pose as a2_pose,
)

DROP = 22.75
BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
WELL = (-450.3, 550.3, -74.3, 74.3, 63.25, 100.0)
SLOTS = (
    (-430.0, 530.0, -100.0, 100.0, 65.7, 70.3),
    (-430.0, 530.0, -100.0, 100.0, 71.2, 75.8),
    (-430.0, 530.0, -100.0, 100.0, 76.2, 80.8),
    (-430.0, 530.0, -100.0, 100.0, 81.7, 86.3),
)
LAYERS = {
    side: tuple(z - DROP for z in heights)
    for side, heights in A2_LAYERS.items()
}


def pose(fraction, side):
    """A2 motion law and in-plane placement; layer heights are in LAYERS."""
    return a2_pose(fraction, side)


def place_panel(panel, side, kind, fraction):
    """Place a panel at its A2 pose, including the approved Z drop."""
    return a2_place_panel(panel, side, kind, fraction).translate((0, 0, -DROP))


def cutters():
    """Return the exact union of the approved well and four layer slots."""
    result = box(*WELL)
    for extents in SLOTS:
        result = result + box(*extents)
    return result.clean()


def body_recessed():
    """Cut the fixed recess from the original A2 body factory output."""
    original = a2_body()
    recessed = (original - cutters()).clean()
    recessed.label = BODY_LABEL
    return recessed


def components(fraction):
    """Return all eleven A2 nonbody components with one rigid Z translation."""
    return [part.translate((0, 0, -DROP)) for part in a2_components(fraction)]


def assembly(fraction, full=True):
    parts = components(fraction)
    if full:
        parts.insert(0, body_recessed())
    return bd.Compound(children=parts, label="Phantom_interleaved_A3")


@step(out="../STEP/O_Interleaved_A3_Stowed.step")
def stowed():
    return assembly(0)


@step(out="../STEP/O_Interleaved_A3_Module_Stowed.step")
def module_stowed():
    return assembly(0, False)


@step(out="../STEP/O_Interleaved_A3_Midfold.step")
def midfold():
    return assembly(0.5)


@step(out="../STEP/O_Interleaved_A3_Deployed.step")
def deployed():
    return assembly(1)


@step(out="../STEP/O_Interleaved_A3_Body_Pocket.step")
def body_pocket():
    return body_recessed()


if __name__ == "__main__":
    stowed()
    module_stowed()
    midfold()
    deployed()
    body_pocket()
