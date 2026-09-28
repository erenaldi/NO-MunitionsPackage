"""R1 sketch-led belly ramp intake, composed onto saved Tail R4 poses."""

from __future__ import annotations

import math
from pathlib import Path

from cadgen import build123d as bd, read_step, srgb, step


ROOT = Path(__file__).resolve().parents[1]
BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
HINGE_X = -950.0
HINGE_Z = -83.0
DEPLOYMENT_DEG = 5.0
BODY_COLOR = srgb("#A7B4BC")
RAMP_COLOR = srgb("#788B96")
HARDWARE_COLOR = srgb("#92999D")

R4_INPUTS = {
    "Stowed": "Q_Tail_R4_Four_Stowed.step",
    "Midfold": "Q_Tail_R4_Four_Midfold.step",
    "Deployed": "Q_Tail_R4_Four_Deployed.step",
}
STATE_FRACTIONS = {"Stowed": 0.0, "Midfold": 0.5, "Deployed": 1.0}


def _make_box(x0, x1, y0, y1, z0, z1):
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
    )


def _cylinder_y(radius, y0, y1):
    return bd.Cylinder(radius, y1 - y0).rotate(bd.Axis.X, 90.0).translate(
        (HINGE_X, (y0 + y1) / 2.0, HINGE_Z)
    )


def _union(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result + shape
    return result.clean()


def _triangle_cheek(y0):
    top_z = HINGE_Z + 650.0 * math.tan(math.radians(DEPLOYMENT_DEG))
    wire = bd.Wire.make_polygon(
        [(-950.0, y0, -83.0), (-300.0, y0, -83.0), (-300.0, y0, top_z)],
        close=True,
    )
    return bd.extrude(bd.Face(wire), amount=2.0, dir=(0.0, 1.0, 0.0))


def cutters():
    """Return the exact fused R1 body-cut tool set from the approved probe."""
    cavity = _make_box(-953.3, -289.7, -64.3, 64.3, -100.0, -25.8)
    aft_stub = _make_box(-1030.0, -953.0, -58.0, 58.0, -77.0, -28.0)
    barrel_relief = _cylinder_y(3.3, -64.3, 64.3)
    shaft_relief = _cylinder_y(1.55, -71.3, 71.3)
    cap_reliefs = (
        _cylinder_y(2.8, -72.3, -71.0),
        _cylinder_y(2.8, 71.0, 72.3),
    )
    return _union([cavity, aft_stub, barrel_relief, shaft_relief, *cap_reliefs])


def _cut_body(original_body):
    body = (original_body - cutters()).clean()
    body.label = BODY_LABEL
    body.color = BODY_COLOR
    return body


def _read_parts(path):
    """Read a saved assembly and retain its styled leaf shapes unchanged."""
    root = read_step(str(path))
    leaves = []

    def visit(node):
        children = list(getattr(node, "children", ()) or ())
        if children:
            for child in children:
                visit(child)
        else:
            leaves.append(node)

    visit(root)
    parts = {}
    for part in leaves:
        label = str(part.label)
        if label in parts:
            raise RuntimeError(f"Duplicate saved STEP label {label!r} in {path}")
        parts[label] = part
    if BODY_LABEL not in parts:
        raise RuntimeError(f"Saved R4 STEP lacks body {BODY_LABEL!r}: {path}")
    return parts


def intake_components(f):
    """Create the fused ramp, two mounts and capped pin at intake fraction f."""
    fraction = float(f)
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"Intake deployment fraction must be in [0, 1], got {f!r}")

    floor = _make_box(-950.0, -290.0, -64.0, 64.0, -86.0, -83.0)
    root_barrel = _cylinder_y(3.0, -64.0, 64.0)
    cheeks = (_triangle_cheek(-64.0), _triangle_cheek(62.0))
    ramp = (_union([floor, root_barrel, *cheeks]) - _cylinder_y(1.5, -64.0, 64.0)).clean()
    if fraction:
        ramp = ramp.rotate(
            bd.Axis((HINGE_X, 0.0, HINGE_Z), (0.0, 1.0, 0.0)),
            DEPLOYMENT_DEG * fraction,
        )
    ramp.label = "intake_r1_ramp"
    ramp.color = RAMP_COLOR

    mounts = []
    for label, y0, y1 in (
        ("intake_r1_fixed_mount_negative_y", -71.0, -65.0),
        ("intake_r1_fixed_mount_positive_y", 65.0, 71.0),
    ):
        foot = _make_box(-953.0, -947.0, y0, y1, -83.0, -75.0)
        bored_mount = (_union([_cylinder_y(3.0, y0, y1), foot])
                       - _cylinder_y(1.5, y0, y1)).clean()
        bored_mount.label = label
        bored_mount.color = HARDWARE_COLOR
        mounts.append(bored_mount)

    shaft = _cylinder_y(1.25, -71.3, 71.3)
    cap_negative = _cylinder_y(2.5, -72.0, -71.3)
    cap_positive = _cylinder_y(2.5, 71.3, 72.0)
    pin = _union([shaft, cap_negative, cap_positive])
    pin.label = "intake_r1_throughpin"
    pin.color = HARDWARE_COLOR

    return [ramp, *mounts, pin]


def _module(state):
    state_name = str(state).title()
    if state_name not in STATE_FRACTIONS or state_name == "Midfold":
        raise ValueError(f"Unknown intake module state: {state!r}")
    parts = intake_components(STATE_FRACTIONS[state_name])
    return bd.Compound(children=parts, label=f"R_RampIntake_R1_Module_{state_name}")


def assembly(state):
    """Compose one saved R4 state, changing only its body and adding the intake."""
    state_name = str(state).title()
    if state_name not in R4_INPUTS:
        raise ValueError(f"Unknown R4 assembly state: {state!r}")
    parts = _read_parts(ROOT / "STEP" / R4_INPUTS[state_name])
    original_body = parts[BODY_LABEL]
    parts[BODY_LABEL] = _cut_body(original_body)
    intake = intake_components(STATE_FRACTIONS[state_name])
    return bd.Compound(
        children=[*parts.values(), *intake],
        label=f"R_RampIntake_R1_{state_name}",
    )


@step(out="../STEP/R_RampIntake_R1_Stowed.step")
def stowed():
    return assembly("Stowed")


@step(out="../STEP/R_RampIntake_R1_Midfold.step")
def midfold():
    return assembly("Midfold")


@step(out="../STEP/R_RampIntake_R1_Deployed.step")
def deployed():
    return assembly("Deployed")


@step(out="../STEP/R_RampIntake_R1_Body_Cavity.step")
def body_cavity():
    stowed_parts = _read_parts(ROOT / "STEP" / R4_INPUTS["Stowed"])
    return _cut_body(stowed_parts[BODY_LABEL])


@step(out="../STEP/R_RampIntake_R1_Module_Stowed.step")
def module_stowed():
    return _module("Stowed")


@step(out="../STEP/R_RampIntake_R1_Module_Deployed.step")
def module_deployed():
    return _module("Deployed")


if __name__ == "__main__":
    stowed()
    midfold()
    deployed()
    body_cavity()
    module_stowed()
    module_deployed()
