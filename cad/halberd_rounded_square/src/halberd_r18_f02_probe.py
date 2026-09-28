"""Saved, cropped R18 F02 native-shoulder probe; no other access features."""
from copy import deepcopy

from cadgen import build123d as bd, step

from halberd_r18_access_shapes import (
    APPROVED_BASE_HASH,
    BASELINE_STEP,
    build_f02_native_preflight,
    load_manifest,
    load_saved_parts,
)
from halberd_r18_layout_base import MATERIALS as R18_BASE_MATERIALS


EXPECTED_LABELS = (
    "main_body_intake_r12_r18_access_cut",
    "r18_F02_cover",
    "r18_F02_fastener_1",
    "r18_F02_fastener_2",
    "r18_F02_fastener_3",
    "r18_F02_fastener_4",
)
F02_MATERIALS = {
    "definitions": deepcopy(R18_BASE_MATERIALS["definitions"]),
    "assignments": [
        {"targets": ["#r18_F02_cover"], "material": "detail_paint"},
        {"targets": [f"#r18_F02_fastener_{index}" for index in range(1, 5)],
         "material": "detail_metal"},
    ],
}


@step(out="../STEP/halberd_r18_f02_probe.step", materials=F02_MATERIALS)
def halberd_r18_f02_probe():
    manifest = load_manifest()
    source_scene, source_parts = load_saved_parts(BASELINE_STEP)
    if source_scene.document_hash != APPROVED_BASE_HASH:
        raise ValueError("F02 probe source is not the approved saved R18 layout base")
    if len(source_parts) != 28 or "main_body_intake_r12" not in source_parts:
        raise ValueError("F02 probe source does not contain the expected saved 28-part base")

    proto = build_f02_native_preflight(source_parts["main_body_intake_r12"], manifest)
    bounds = proto.host_before.bounding_box()
    context_box = bd.Box(
        190.0, bounds.size.Y + 2.0, bounds.size.Z + 2.0
    ).translate((900.0,
                 (bounds.min.Y + bounds.max.Y) / 2.0,
                 (bounds.min.Z + bounds.max.Z) / 2.0))
    focused_host = proto.host_after & context_box
    if not focused_host or not focused_host.is_valid or len(focused_host.solids()) != 1:
        raise ValueError("F02 cropped changed host is empty, invalid, or not one solid")
    focused_host.label = "main_body_intake_r12_r18_access_cut"
    focused_host.color = proto.host_after.color

    parts = [focused_host, *proto.parts]
    if tuple(part.label for part in parts) != EXPECTED_LABELS:
        raise ValueError("F02 saved focus labels do not match the six-part contract")
    if any(part.bounding_box().min.X < 805.0 - 0.05 or
           part.bounding_box().max.X > 995.0 + 0.05 for part in parts):
        raise ValueError("An F02 probe part lies outside the authorized axial focus crop")
    return bd.Compound(children=parts, label="Halberd_R18_F02_Curved_Shoulder_Probe")


if __name__ == "__main__":
    halberd_r18_f02_probe()
