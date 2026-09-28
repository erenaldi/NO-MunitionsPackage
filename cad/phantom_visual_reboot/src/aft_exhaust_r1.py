"""Aft-exhaust R1 implementation composed onto the immutable Intake R3 poses."""

from __future__ import annotations

from pathlib import Path

from cadgen import build123d as bd, read_step, srgb, step


ROOT = Path(__file__).resolve().parents[1]
BODY_LABEL = "RDM9_R7_symmetric_body_20mm_wedge_R4"
LINER_LABEL = "aft_exhaust_r1_liner"
STATE_NAMES = ("Stowed", "Midfold", "Deployed")

OUTER_SECTIONS = (
    (-1394.0, 124.0, 124.0, 0.0, 14.0),
    (-1360.0, 110.0, 110.0, 0.0, 12.0),
    (-1310.0, 84.0, 84.0, 0.0, 10.0),
)
INNER_SECTIONS = (
    (-1394.0, 116.0, 116.0, 0.0, 10.0),
    (-1360.0, 102.0, 102.0, 0.0, 8.0),
    (-1310.0, 76.0, 76.0, 0.0, 6.0),
)
CONNECTOR_SECTIONS = (
    (-1310.5, 76.0, 76.0, 0.0, 6.0),
    (-1308.0, 76.0, 76.0, 0.0, 6.0),
    (-1270.0, 80.0, 70.0, -10.0, 6.0),
    (-1150.0, 100.0, 60.0, -35.0, 6.0),
    (-1029.5, 116.0, 49.0, -52.5, 5.0),
)
SEAT_SECTIONS = (
    (-1401.0, 124.0, 124.0, 0.0, 14.0),
    (-1394.0, 124.0, 124.0, 0.0, 14.0),
    *OUTER_SECTIONS[1:],
)
INNER_TOOL_SECTIONS = (
    (-1395.0, 116.0, 116.0, 0.0, 10.0),
    *INNER_SECTIONS,
    (-1309.0, 76.0, 76.0, 0.0, 6.0),
)
LINER_COLOR = srgb("#555555")


def rounded_section(record):
    """Make a rounded section at X; record is (X, widthY, heightZ, centerZ, radius)."""
    x, width_y, height_z, center_z, radius = record
    # RectangleRounded is in local XY. Rotation maps local X to world Z and
    # local Y to world Y; passing height first preserves the requested axes.
    profile = bd.RectangleRounded(height_z, width_y, radius)
    profile = profile.rotate(bd.Axis.Y, 90.0).translate((x, 0.0, center_z))
    return profile.faces()[0].outer_wire()


def ruled_loft(records):
    """Create a ruled loft from the declared X/widthY/heightZ section tuples."""
    return bd.Solid.make_loft([rounded_section(row) for row in records], ruled=True)


def outer_liner():
    return ruled_loft(OUTER_SECTIONS)


def inner_liner_tool():
    """Open both liner ends with the specified 1 mm overrun at each end."""
    return ruled_loft(INNER_TOOL_SECTIONS)


def liner():
    result = (outer_liner() - inner_liner_tool()).clean()
    result.label = LINER_LABEL
    result.color = LINER_COLOR
    return result


def seat_cutter():
    return ruled_loft(SEAT_SECTIONS)


def connector_cutter():
    return ruled_loft(CONNECTOR_SECTIONS)


def body_cutters():
    """Union the rear seat and connector passage cutters."""
    return (seat_cutter() + connector_cutter()).clean()


def cut_body(original_body):
    result = (original_body - body_cutters()).clean()
    result.label = BODY_LABEL
    # Keep the existing R3 body appearance through the Boolean replacement.
    result.color = original_body.color
    return result


def _read_parts(state):
    """Read a saved R3 STEP as a tracked input, retaining styled leaf parts."""
    path = ROOT / "STEP" / f"R_RampIntake_R3_{state}.step"
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
        raise RuntimeError(f"Saved R3 STEP lacks body {BODY_LABEL!r}: {path}")
    return parts


def _assembly(state):
    parts = _read_parts(state)
    parts[BODY_LABEL] = cut_body(parts[BODY_LABEL])
    parts[LINER_LABEL] = liner()
    return bd.Compound(children=list(parts.values()), label=f"S_AftExhaust_R1_{state}")


@step(out="../STEP/S_AftExhaust_R1_Stowed.step")
def stowed():
    return _assembly("Stowed")


@step(out="../STEP/S_AftExhaust_R1_Midfold.step")
def midfold():
    return _assembly("Midfold")


@step(out="../STEP/S_AftExhaust_R1_Deployed.step")
def deployed():
    return _assembly("Deployed")


@step(out="../STEP/S_AftExhaust_R1_Body_Duct.step")
def body_duct():
    parts = _read_parts("Stowed")
    return cut_body(parts[BODY_LABEL])


@step(out="../STEP/S_AftExhaust_R1_Liner.step")
def liner_step():
    return liner()


if __name__ == "__main__":
    stowed()
    midfold()
    deployed()
    body_duct()
    liner_step()
