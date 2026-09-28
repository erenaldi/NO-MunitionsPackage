"""A4 — restore the unused opposite-side channels in the A3 recessed body.

The body is the original A2 factory output minus the A3 central well and four
side-restricted slots. All nonbody parts are reused unchanged from A3.
"""
from cadgen import build123d as bd, step
from interleaved_wing_a2 import body as a2_body, box
from interleaved_wing_a3 import components as a3_components

BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
WELL = (-450.3, 550.3, -74.3, 74.3, 63.25, 100.0)
SLOTS = (
    (-430.0, 530.0, 0.0, 100.0, 65.7, 70.3),
    (-430.0, 530.0, 0.0, 100.0, 76.2, 80.8),
    (-430.0, 530.0, -100.0, 0.0, 71.2, 75.8),
    (-430.0, 530.0, -100.0, 0.0, 81.7, 86.3),
)


def cutters():
    """Return the A3 well and A4's four side-restricted slot cutters."""
    result = box(*WELL)
    for extents in SLOTS:
        result = result + box(*extents)
    return result.clean()


def body_recessed():
    """Cut the A4 recess from the original A2 body factory output."""
    recessed = (a2_body() - cutters()).clean()
    recessed.label = BODY_LABEL
    return recessed


def components(fraction):
    """Return the A3 nonbody components without additional transforms."""
    return a3_components(fraction)


def assembly(fraction, full=True):
    parts = components(fraction)
    if full:
        parts.insert(0, body_recessed())
    return bd.Compound(children=parts, label="Phantom_interleaved_A4")


@step(out="../STEP/O_Interleaved_A4_Stowed.step")
def stowed():
    return assembly(0)


@step(out="../STEP/O_Interleaved_A4_Module_Stowed.step")
def module_stowed():
    return assembly(0, False)


@step(out="../STEP/O_Interleaved_A4_Midfold.step")
def midfold():
    return assembly(0.5)


@step(out="../STEP/O_Interleaved_A4_Deployed.step")
def deployed():
    return assembly(1)


@step(out="../STEP/O_Interleaved_A4_Body_Pocket.step")
def body_pocket():
    return body_recessed()


if __name__ == "__main__":
    stowed()
    module_stowed()
    midfold()
    deployed()
    body_pocket()
