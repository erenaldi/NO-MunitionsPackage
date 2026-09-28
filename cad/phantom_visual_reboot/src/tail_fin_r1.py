"""Reversible one-corner R1 tail-fin planform prototypes on saved A5 states."""

from __future__ import annotations

from pathlib import Path

from cadgen import build123d as bd, read_step, srgb, step


ROOT = Path(__file__).resolve().parents[1]
HINGE_Y = 82.0
HINGE_Z = 88.5
ROOT_X = (-1245.0, -1005.0)
FIXED_X = ((-1255.0, -1246.0), (-1004.0, -995.0))
PIN_SHAFT_X = (-1255.3, -994.7)
CAP_X = ((-1256.0, -1255.3), (-994.7, -994.0))
FOLD_ANGLE_DEG = -135.0
PANEL_Z = (87.0, 90.0)
PLANFORMS = {
    "Compact": ((-1245.0, 0.0), (-1005.0, 0.0), (-1105.0, 70.0), (-1210.0, 70.0)),
    "Swept": ((-1245.0, 0.0), (-1005.0, 0.0), (-1195.0, 90.0), (-1230.0, 90.0)),
    "Tall": ((-1245.0, 0.0), (-1005.0, 0.0), (-1100.0, 110.0), (-1200.0, 110.0)),
}
A5_STATES = {
    "Stowed": ("O_Interleaved_A5_Stowed.step", 0.0),
    "Midfold": ("O_Interleaved_A5_Midfold.step", 0.5),
    "Deployed": ("O_Interleaved_A5_Deployed.step", 1.0),
}


def _variant_name(variant: str) -> str:
    for name in PLANFORMS:
        if name.lower() == str(variant).lower():
            return name
    raise ValueError(f"Unknown tail-fin R1 variant: {variant!r}")


def _state_name(state: str) -> str:
    for name in A5_STATES:
        if name.lower() == str(state).lower():
            return name
    raise ValueError(f"Unknown tail-fin R1 state: {state!r}")


def _cylinder_x(radius: float, x0: float, x1: float, y: float, z: float):
    return bd.Cylinder(
        radius,
        x1 - x0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER),
    ).rotate(bd.Axis.Y, 90.0).translate(((x0 + x1) / 2.0, y, z))


def fin_stowed(variant: str):
    """Return one selected rough panel/root solid at its stowed datum."""
    name = _variant_name(variant)
    points = [
        (x, HINGE_Y - inward_span, PANEL_Z[0])
        for x, inward_span in PLANFORMS[name]
    ]
    panel = bd.extrude(
        bd.Face(bd.Wire.make_polygon(points, close=True)),
        amount=PANEL_Z[1] - PANEL_Z[0],
        dir=(0, 0, 1),
    )
    root_tube = _cylinder_x(3.0, *ROOT_X, HINGE_Y, HINGE_Z)
    blank = (panel + root_tube).clean()
    bore = _cylinder_x(1.5, ROOT_X[0] - 0.1, ROOT_X[1] + 0.1, HINGE_Y, HINGE_Z)
    fin = (blank - bore).clean()
    fin.label = "tail_r1_fin_root"
    fin.color = srgb("#71899A")
    return fin


def hardware():
    """Return the two fixed foot/knuckles and common capped through-pin."""
    fixed_parts = []
    for label, (x0, x1) in zip(
        ("tail_r1_fixed_knuckle_aft", "tail_r1_fixed_knuckle_forward"),
        FIXED_X,
    ):
        foot = bd.Solid.make_box(
            x1 - x0,
            84.5 - 79.0,
            88.5 - 80.0,
            plane=bd.Plane(origin=(x0, 79.0, 80.0)),
        )
        knuckle = _cylinder_x(3.0, x0, x1, HINGE_Y, HINGE_Z)
        joined = (foot + knuckle).clean()
        bore = _cylinder_x(1.5, x0 - 0.1, x1 + 0.1, HINGE_Y, HINGE_Z)
        fixed = (joined - bore).clean()
        fixed.label = label
        fixed.color = srgb("#A7B4BC")
        fixed_parts.append(fixed)

    shaft = _cylinder_x(1.25, *PIN_SHAFT_X, HINGE_Y, HINGE_Z)
    caps = [
        _cylinder_x(2.5, x0, x1, HINGE_Y, HINGE_Z)
        for x0, x1 in CAP_X
    ]
    pin = (shaft + caps[0] + caps[1]).clean()
    pin.label = "tail_r1_throughpin"
    pin.color = srgb("#596A76")
    return [*fixed_parts, pin]


def tail_components(variant: str, f: float):
    """Return fin plus stationary hardware at normalized fold fraction f."""
    if not 0.0 <= float(f) <= 1.0:
        raise ValueError(f"Fold fraction must be between 0 and 1; got {f!r}")
    fin = fin_stowed(variant)
    if f:
        fin = fin.rotate(
            bd.Axis((0.0, HINGE_Y, HINGE_Z), (1.0, 0.0, 0.0)),
            FOLD_ANGLE_DEG * float(f),
        )
        fin.label = "tail_r1_fin_root"
        fin.color = srgb("#71899A")
    return [fin, *hardware()]


def assembly(variant: str, state: str):
    """Add the four new parts to the corresponding immutable saved A5 STEP."""
    state_name = _state_name(state)
    a5_filename, fraction = A5_STATES[state_name]
    a5_shape = read_step(str(ROOT / "STEP" / a5_filename))
    return bd.Compound(
        children=[a5_shape, *tail_components(variant, fraction)],
        label=f"Q_Tail_R1_{_variant_name(variant)}_{state_name}",
    )


@step(out="../STEP/Q_Tail_R1_Compact_Stowed.step")
def compact_stowed():
    return assembly("Compact", "Stowed")


@step(out="../STEP/Q_Tail_R1_Compact_Midfold.step")
def compact_midfold():
    return assembly("Compact", "Midfold")


@step(out="../STEP/Q_Tail_R1_Compact_Deployed.step")
def compact_deployed():
    return assembly("Compact", "Deployed")


@step(out="../STEP/Q_Tail_R1_Swept_Stowed.step")
def swept_stowed():
    return assembly("Swept", "Stowed")


@step(out="../STEP/Q_Tail_R1_Swept_Midfold.step")
def swept_midfold():
    return assembly("Swept", "Midfold")


@step(out="../STEP/Q_Tail_R1_Swept_Deployed.step")
def swept_deployed():
    return assembly("Swept", "Deployed")


@step(out="../STEP/Q_Tail_R1_Tall_Stowed.step")
def tall_stowed():
    return assembly("Tall", "Stowed")


@step(out="../STEP/Q_Tail_R1_Tall_Midfold.step")
def tall_midfold():
    return assembly("Tall", "Midfold")


@step(out="../STEP/Q_Tail_R1_Tall_Deployed.step")
def tall_deployed():
    return assembly("Tall", "Deployed")


if __name__ == "__main__":
    compact_stowed()
    compact_midfold()
    compact_deployed()
    swept_stowed()
    swept_midfold()
    swept_deployed()
    tall_stowed()
    tall_midfold()
    tall_deployed()
