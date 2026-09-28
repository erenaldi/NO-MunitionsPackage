"""Read-only crop of the selected Kris STEP around its front section joints."""
from pathlib import Path

from cadgen import build123d as bd, read_step, step

SOURCE = Path(__file__).resolve().parents[1].parent / "IRM-S4_Kris_PL10_Hybrid.step"
BODY_LABEL = "body_section_5"
CONTEXT_LABELS = ("near_side_panel_border", "near_side_dark_panel")
SEAM_LABELS = ("front_section_seam_1", "front_section_seam_2")
FASTENER_LABELS = tuple(
    f"front_joint_fastener_{face}_{row}"
    for face in range(1, 5)
    for row in (1, 2)
)
PART_LABELS = (BODY_LABEL, *CONTEXT_LABELS, *SEAM_LABELS, *FASTENER_LABELS)
CLIP_CENTER_Z = 2411.


@step(out="../STEP/kris_joint_reference.step")
def kris_joint_reference():
    model = read_step(SOURCE)
    by_label = {part.label: part for part in model.children}
    missing = set(PART_LABELS) - set(by_label)
    if missing:
        raise ValueError(f"Kris reference is missing source parts: {sorted(missing)}")
    clip = bd.Box(180., 180., 70.).translate((0., 0., CLIP_CENTER_Z))
    parts = []
    for label in PART_LABELS:
        source_part = by_label[label]
        cropped = source_part & clip
        if not cropped or cropped.volume <= 0.:
            raise ValueError(f"Selected Kris crop is empty: {label}")
        cropped = cropped.rotate(bd.Axis.Y, -90.).translate((CLIP_CENTER_Z, 0., 0.))
        cropped.label = label
        cropped.color = source_part.color
        parts.append(cropped)
    return bd.Compound(children=parts, label="Kris_Front_Joint_Reference_Crop")


if __name__ == "__main__":
    kris_joint_reference()
