"""R16: one nose/body joint liner and four recessed fasteners on R15."""
from copy import deepcopy

from cadgen import build123d as bd
from cadgen import srgb

from halberd_r13_shapes import panel_parts as r13_panel_parts
from halberd_r15 import halberd_r15
from halberd_r15_shapes import MATERIALS as R15_MATERIALS

MAIN_LABEL = "main_body_intake_r12"
LINER_LABEL = "main_joint_liner_1"
FASTENERS = tuple(f"main_joint_fastener_{i}" for i in range(1, 5))
JOINT_LABELS = (LINER_LABEL, *FASTENERS)
FOCUS_LABELS = (MAIN_LABEL, "main_ogive", *JOINT_LABELS)
CLOCKS = (0., 90., 180., 270.)
FOCUS_CENTER_X = 1085.

MATERIALS = deepcopy(R15_MATERIALS)
MATERIALS["assignments"].append({
    "targets": [f"#{label}" for label in JOINT_LABELS],
    "material": "detail_metal",
})
FOCUS_MATERIALS = {
    "definitions": {"detail_metal": MATERIALS["definitions"]["detail_metal"]},
    "assignments": [MATERIALS["assignments"][-1]],
}


def cylinder_x(radius, x0, x1):
    return bd.Cylinder(radius, x1 - x0,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .rotate(bd.Axis.Y, 90).translate((x0, 0, 0))


def joint_pocket():
    outer = cylinder_x(120., 1083.7, 1085.)
    inner = cylinder_x(94.4, 1083.7, 1085.)
    return outer - inner


def fastener_seat(clock):
    bore = bd.Cylinder(1.36, .6,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .translate((1078., 0., 93.5))
    countersink = bd.Cone(1.36, 2.576, 1.2,
                          align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) \
        .translate((1078., 0., 94.1))
    return (bore + countersink).rotate(bd.Axis.X, -clock)


def liner_shape():
    outer = cylinder_x(94.8, 1083.8, 1084.9)
    inner = cylinder_x(94.4, 1083.8, 1084.9)
    liner = outer - inner
    liner.label = LINER_LABEL
    liner.color = srgb("#87939B")
    return liner


def _base_parts():
    model = halberd_r15()
    parts = {p.label: p for p in model.children}
    if len(parts) != len(model.children) or MAIN_LABEL not in parts:
        raise ValueError("Unexpected R15 composition or duplicate labels")
    return model, parts


def build_r16(separated=False):
    _, baseline = _base_parts()
    main = baseline[MAIN_LABEL] - joint_pocket()
    for clock in CLOCKS:
        main = main - fastener_seat(clock)
    main.label = MAIN_LABEL
    main.color = baseline[MAIN_LABEL].color

    parts = [main]
    for label, part in baseline.items():
        if label == MAIN_LABEL:
            continue
        if separated and label.startswith("booster"):
            part = part.moved(bd.Location((-340., 0., 0.)))
        parts.append(part)

    liner = liner_shape()
    parts.append(liner)
    original_fastener = r13_panel_parts()[2]
    for label, clock in zip(FASTENERS, CLOCKS):
        fastener = original_fastener.moved(bd.Location((1446., 0., -5.))) \
            .rotate(bd.Axis.X, -clock)
        fastener.label = label
        fastener.color = original_fastener.color
        parts.append(fastener)

    if len(parts) != 44:
        raise ValueError(f"Unexpected R16 part count: {len(parts)}")
    suffix = "_Separated" if separated else ""
    return bd.Compound(children=parts, label=f"Halberd_R16_Nose_Body_Joint{suffix}")


def focus(model):
    clip = bd.Box(160., 240., 240.).translate((FOCUS_CENTER_X, 0., 0.))
    parts = []
    by_label = {p.label: p for p in model.children}
    if set(FOCUS_LABELS) - set(by_label):
        raise ValueError("R16 focus source is missing a selected part")
    for label in FOCUS_LABELS:
        part = by_label[label]
        cropped = part & clip
        cropped.label = label
        cropped.color = part.color
        parts.append(cropped)
    return bd.Compound(children=parts, label="Halberd_R16_Nose_Body_Joint_Focus")
