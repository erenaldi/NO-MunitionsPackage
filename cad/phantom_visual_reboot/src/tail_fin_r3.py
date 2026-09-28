"""Tail R3: aft-shifted clipped fin with a matching shaped body recess."""

from __future__ import annotations

from pathlib import Path

from cadgen import build123d as bd, read_step, srgb, step
from tail_fin_r1 import A5_STATES, PLANFORMS, ROOT, hardware


BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
FIN_LABEL = "tail_r1_fin_root"
SUPPORT_LABELS = ("tail_r1_fixed_knuckle_aft", "tail_r1_fixed_knuckle_forward")
PIN_LABEL = "tail_r1_throughpin"
TAIL_LABELS = (FIN_LABEL, *SUPPORT_LABELS, PIN_LABEL)
A5_LABELS = (
    BODY_LABEL,
    "port_carriage", "port_fixed_root", "port_front", "port_join", "port_rear",
    "starboard_carriage", "starboard_fixed_root", "starboard_front", "starboard_join", "starboard_rear",
    "supported_housing", "top_cover",
)

AFT_SHIFT_X = -80.0
HARDWARE_DROP_Z = -5.5
ROOT_X = (-1325.0, -1085.0)
HINGE_Y = 82.0
HINGE_Z = 83.0
FOLD_ANGLE_DEG = -135.0
PANEL_Z = (83.0, 86.0)
POCKET_Z = (82.7, 100.0)
POCKET_OFFSET = 0.3


def _cylinder_x(radius: float, x0: float, x1: float, y: float, z: float):
    return bd.Cylinder(
        radius,
        x1 - x0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER),
    ).rotate(bd.Axis.Y, 90.0).translate(((x0 + x1) / 2.0, y, z))


def _tall_planform_xy():
    return tuple((x + AFT_SHIFT_X, HINGE_Y - span) for x, span in PLANFORMS["Tall"])


def pocket_cutters():
    """Return the probe-approved shaped panel pocket and coaxial relief tools."""
    outline = bd.Wire.make_polygon(
        [(x, y, 0.0) for x, y in _tall_planform_xy()],
        close=True,
    )
    expanded_outline = outline.offset_2d(
        POCKET_OFFSET,
        kind=bd.Kind.ARC,
        side=bd.Side.BOTH,
        closed=True,
    )
    shaped_pocket = bd.extrude(
        bd.Face(expanded_outline),
        amount=POCKET_Z[1] - POCKET_Z[0],
        dir=(0, 0, 1),
    ).translate((0.0, 0.0, POCKET_Z[0]))

    hinge_relief = _cylinder_x(3.3, ROOT_X[0] - 0.3, ROOT_X[1] + 0.3, HINGE_Y, HINGE_Z)
    shaft_relief = _cylinder_x(1.55, -1335.6, -1074.4, HINGE_Y, HINGE_Z)
    cap_reliefs = (
        _cylinder_x(2.8, -1336.3, -1335.0, HINGE_Y, HINGE_Z),
        _cylinder_x(2.8, -1075.0, -1073.7, HINGE_Y, HINGE_Z),
    )
    return [shaped_pocket, hinge_relief, shaft_relief, *cap_reliefs]


def _recessed_body(body):
    cutters = pocket_cutters()
    cutter_union = cutters[0]
    for cutter in cutters[1:]:
        cutter_union = cutter_union + cutter
    cutter_union = cutter_union.clean()
    recessed = (body - cutter_union).clean()
    recessed.label = BODY_LABEL
    recessed.color = srgb('#A7B4BC')
    return recessed


def fin_stowed():
    """Return the Tall clipped panel and root barrel at the R3 hinge datum."""
    points = [(x, y, PANEL_Z[0]) for x, y in _tall_planform_xy()]
    panel = bd.extrude(
        bd.Face(bd.Wire.make_polygon(points, close=True)),
        amount=PANEL_Z[1] - PANEL_Z[0],
        dir=(0, 0, 1),
    )
    root_barrel = _cylinder_x(3.0, *ROOT_X, HINGE_Y, HINGE_Z)
    pin_bore = _cylinder_x(1.5, ROOT_X[0] - 0.1, ROOT_X[1] + 0.1, HINGE_Y, HINGE_Z)
    fin = ((panel + root_barrel).clean() - pin_bore).clean()
    fin.label = FIN_LABEL
    fin.color = srgb('#71899A')
    return fin


def tail_components(f: float):
    """Return the moving fin and fixed R1-derived hardware at fold fraction f."""
    fraction = float(f)
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"Fold fraction must be between 0 and 1; got {f!r}")

    fin = fin_stowed()
    if fraction:
        fin = fin.rotate(
            bd.Axis((0.0, HINGE_Y, HINGE_Z), (1.0, 0.0, 0.0)),
            FOLD_ANGLE_DEG * fraction,
        )
        fin.label = FIN_LABEL

    fixed_hardware = [
        part.translate((AFT_SHIFT_X, 0.0, HARDWARE_DROP_Z))
        for part in hardware()
    ]
    return [fin, *fixed_hardware]


def _flatten_saved_step(path: Path):
    """Read saved assembly leaves as individually labeled solids."""
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
        solids = list(part.solids())
        if len(solids) != 1:
            raise RuntimeError(f"Expected one solid for saved STEP part {label!r}; found {len(solids)}")
        parts[label] = part
    missing = sorted(set(A5_LABELS) - set(parts))
    if missing:
        raise RuntimeError(f"Missing saved A5 STEP parts in {path}: {missing}")
    return parts


def assembly(state: str):
    """Replace only the saved A5 body, retaining its 12 peers and adding the tail."""
    state_name = next((name for name in A5_STATES if name.lower() == str(state).lower()), None)
    if state_name is None:
        raise ValueError(f"Unknown A5 state: {state!r}")
    filename, fraction = A5_STATES[state_name]
    parts = _flatten_saved_step(ROOT / "STEP" / filename)
    parts[BODY_LABEL] = _recessed_body(parts[BODY_LABEL])
    ordered_a5 = [parts[label] for label in A5_LABELS]
    tail = tail_components(fraction)
    for expected, part in zip(TAIL_LABELS, tail):
        part.label = expected
    return bd.Compound(
        children=[*ordered_a5, *tail],
        label=f"Q_Tail_R3_Recessed_{state_name}",
    )


@step(out='../STEP/Q_Tail_R3_Recessed_Stowed.step')
def stowed():
    return assembly('Stowed')


@step(out='../STEP/Q_Tail_R3_Recessed_Midfold.step')
def midfold():
    return assembly('Midfold')


@step(out='../STEP/Q_Tail_R3_Recessed_Deployed.step')
def deployed():
    return assembly('Deployed')


@step(out='../STEP/Q_Tail_R3_Recessed_Body_Pocket.step')
def body_pocket():
    stowed_parts = _flatten_saved_step(ROOT / "STEP" / A5_STATES["Stowed"][0])
    return _recessed_body(stowed_parts[BODY_LABEL])


if __name__ == "__main__":
    stowed()
    midfold()
    deployed()
    body_pocket()
