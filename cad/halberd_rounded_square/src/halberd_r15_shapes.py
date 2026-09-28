"""R15: propagate the R13 service-cover family to the other three cardinal flats.

The approved R13 four-part cover assembly (seat, cover, recessed border, two
slotted fasteners) is copied through rigid X-axis rotations onto the 90/180/270
degree flat faces. The main body only loses the three new 124x30x1.2 mm seats;
every R14 junction and all 26 non-body baseline parts are preserved exactly.
Intake/fin stations remain the separate diagonal set at 45/135/225/315 degrees.
"""
from copy import deepcopy
from cadgen import build123d as bd
from study_shapes import tag, SEPARATION
from halberd_r12_shapes import MAIN_LABEL, MATERIALS as BASE_MATERIALS
from halberd_r13_shapes import pocket
from halberd_r14_shapes import build_r14

PANEL_X = -320.
CLOCKS = (90., 180., 270.)
COVERS = tuple(f"main_service_cover_{i}" for i in range(1, 5))
BORDERS = tuple(f"main_service_border_{i}" for i in range(1, 5))
FASTENERS = tuple(f"main_service_fastener_{i}" for i in range(1, 9))
SERVICE_LABELS = COVERS + BORDERS + FASTENERS

MATERIALS = deepcopy(BASE_MATERIALS)
MATERIALS["definitions"].update({
    "detail_paint": {"name": "Service cover paint", "roughness": .65, "metalness": .15},
    "detail_border": {"name": "Recessed joint", "roughness": .9, "metalness": .05},
    "detail_metal": {"name": "Small metallic hardware", "roughness": .38, "metalness": .65},
})
MATERIALS["assignments"].extend([
    {"targets": [f"#main_service_cover_{i}" for i in range(1, 5)], "material": "detail_paint"},
    {"targets": [f"#main_service_border_{i}" for i in range(1, 5)], "material": "detail_border"},
    {"targets": [f"#main_service_fastener_{i}" for i in range(1, 9)], "material": "detail_metal"},
])


def build_r15(separated=False):
    model = build_r14()
    by_label = {p.label: p for p in model.children}
    main = by_label[MAIN_LABEL]
    for clock in CLOCKS:
        main = main - pocket().rotate(bd.Axis.X, -clock)
    main.label = MAIN_LABEL
    main.color = by_label[MAIN_LABEL].color
    parts = [main]
    parts.extend(p for label, p in by_label.items() if label != MAIN_LABEL)
    for i, clock in enumerate(CLOCKS, 2):
        cover = by_label["main_service_cover_1"].rotate(bd.Axis.X, -clock)
        cover.label = f"main_service_cover_{i}"
        border = by_label["main_service_border_1"].rotate(bd.Axis.X, -clock)
        border.label = f"main_service_border_{i}"
        parts.append(cover)
        parts.append(border)
        for j, base in enumerate(("main_service_fastener_1", "main_service_fastener_2"), 2 * i - 1):
            screw = by_label[base].rotate(bd.Axis.X, -clock)
            screw.label = f"main_service_fastener_{j}"
            parts.append(screw)
    if len(parts) != 39:
        raise ValueError("Unexpected R15 part count")
    if separated:
        parts = [p.moved(bd.Location((-SEPARATION, 0, 0)))
                 if p.label.startswith("booster") else p for p in parts]
    return bd.Compound(children=parts, label="Halberd_R15_Four_Face_Service_Covers" +
                       ("_Separated" if separated else ""))


def focus(model):
    # 220 mm axial crop centered on the panel station, full YZ cross-section.
    clip = bd.Box(220., 320., 320.).translate((PANEL_X, 0, 0))
    parts = []
    for p in model.children:
        if p.label not in (MAIN_LABEL, *SERVICE_LABELS):
            continue
        shape = p & clip
        shape.label = p.label
        shape.color = p.color
        parts.append(shape)
    return bd.Compound(children=parts, label="Halberd_R15_Four_Face_Service_Focus")


FOCUS_MATERIALS = {"definitions": MATERIALS["definitions"], "assignments": MATERIALS["assignments"][-3:]}