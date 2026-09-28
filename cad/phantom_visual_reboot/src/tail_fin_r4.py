"""Fourfold propagation of the approved recessed R3 tail fin."""

from __future__ import annotations

from pathlib import Path

from cadgen import build123d as bd, read_step, srgb, step
from tail_fin_r1 import A5_STATES, ROOT
from tail_fin_r3 import A5_LABELS, BODY_LABEL, pocket_cutters, tail_components as r3_tail_components


STATION_ANGLES = {
    "upper_starboard": 0.0,
    "upper_port": 90.0,
    "lower_port": 180.0,
    "lower_starboard": 270.0,
}
_COMPONENT_SUFFIXES = (
    "fin_root",
    "fixed_knuckle_aft",
    "fixed_knuckle_forward",
    "throughpin",
)


def _rotate_global_x(shape, angle: float):
    return shape.rotate(bd.Axis((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)), angle)


def tail_components(f: float):
    """Return four station-rotated copies of the R3 tail set at fold fraction f."""
    fraction = float(f)
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"Fold fraction must be between 0 and 1; got {f!r}")

    components = []
    for station, angle in STATION_ANGLES.items():
        local_parts = r3_tail_components(fraction)
        if len(local_parts) != len(_COMPONENT_SUFFIXES):
            raise RuntimeError(
                f"Expected {len(_COMPONENT_SUFFIXES)} R3 tail parts; found {len(local_parts)}"
            )
        for suffix, part in zip(_COMPONENT_SUFFIXES, local_parts):
            placed = _rotate_global_x(part, angle)
            placed.label = f"tail_r4_{station}_{suffix}"
            components.append(placed)
    return components


def body_recessed(inputbody):
    """Subtract the four station-rotated R3 recess cutter sets from the A5 body."""
    rotated_cutters = [
        _rotate_global_x(cutter, angle)
        for angle in STATION_ANGLES.values()
        for cutter in pocket_cutters()
    ]
    cutter_union = rotated_cutters[0]
    for cutter in rotated_cutters[1:]:
        cutter_union = cutter_union + cutter
    recessed = (inputbody - cutter_union.clean()).clean()
    recessed.label = BODY_LABEL
    recessed.color = srgb("#A7B4BC")
    return recessed


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
    """Replace only the saved A5 body and add all sixteen propagated tail parts."""
    state_name = next((name for name in A5_STATES if name.lower() == str(state).lower()), None)
    if state_name is None:
        raise ValueError(f"Unknown A5 state: {state!r}")
    filename, fraction = A5_STATES[state_name]
    parts = _flatten_saved_step(ROOT / "STEP" / filename)
    parts[BODY_LABEL] = body_recessed(parts[BODY_LABEL])
    ordered_a5 = [parts[label] for label in A5_LABELS]
    return bd.Compound(
        children=[*ordered_a5, *tail_components(fraction)],
        label=f"Q_Tail_R4_Four_{state_name}",
    )


@step(out="../STEP/Q_Tail_R4_Four_Stowed.step")
def stowed():
    return assembly("Stowed")


@step(out="../STEP/Q_Tail_R4_Four_Midfold.step")
def midfold():
    return assembly("Midfold")


@step(out="../STEP/Q_Tail_R4_Four_Deployed.step")
def deployed():
    return assembly("Deployed")


@step(out="../STEP/Q_Tail_R4_Four_Body_Pocket.step")
def body_pocket():
    stowed_parts = _flatten_saved_step(ROOT / "STEP" / A5_STATES["Stowed"][0])
    return body_recessed(stowed_parts[BODY_LABEL])


if __name__ == "__main__":
    stowed()
    midfold()
    deployed()
    body_pocket()
