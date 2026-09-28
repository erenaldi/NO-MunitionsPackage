"""R18 presentation base: R16 with only the old service-cover seats restored."""
from copy import deepcopy
from pathlib import Path

from cadgen import build123d as bd, read_scene, step

from halberd_r16_shapes import FASTENERS, MAIN_LABEL, MATERIALS as R16_MATERIALS


ROOT = Path(__file__).resolve().parents[1]
REMOVED_PREFIX = "main_service_"
RESTORATION_CENTER = (-320.0, 0.0, 0.0)
RESTORATION_SIZE = (200.0, 400.0, 400.0)

MATERIALS = deepcopy(R16_MATERIALS)
filtered_assignments = []
for assignment in MATERIALS["assignments"]:
    kept_targets = [target for target in assignment["targets"]
                    if not target.lstrip("#").startswith(REMOVED_PREFIX)]
    if kept_targets:
        clean_assignment = deepcopy(assignment)
        clean_assignment["targets"] = kept_targets
        filtered_assignments.append(clean_assignment)
MATERIALS["assignments"] = filtered_assignments


def saved_parts(scene):
    leaves = tuple(scene.leaves())
    parts = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in leaves}
    if len(parts) != len(leaves):
        raise ValueError("Saved STEP has duplicate leaf labels")
    return parts


@step(out="../STEP/halberd_r18_layout_base.step", materials=MATERIALS)
def halberd_r18_layout_base():
    r16_scene = read_scene(ROOT / "STEP" / "halberd_r16.step")
    r12_scene = read_scene(ROOT / "STEP" / "halberd_r12.step")
    r16 = saved_parts(r16_scene)
    r12 = saved_parts(r12_scene)
    if MAIN_LABEL not in r16 or MAIN_LABEL not in r12:
        raise ValueError("R12/R16 saved inputs are missing the main body")

    delta = (r12[MAIN_LABEL] - r16[MAIN_LABEL]) & bd.Box(*RESTORATION_SIZE).translate(
        RESTORATION_CENTER)
    main = r16[MAIN_LABEL] + delta
    main.label = MAIN_LABEL
    main.color = r16[MAIN_LABEL].color

    parts = [main]
    parts.extend(part for label, part in r16.items()
                 if label != MAIN_LABEL and not label.startswith(REMOVED_PREFIX))
    expected_labels = set(r16) - {label for label in r16 if label.startswith(REMOVED_PREFIX)}
    if len(expected_labels) != 28 or len(parts) != len(expected_labels):
        raise ValueError(f"Unexpected R18 layout-base composition: {len(parts)} parts")
    return bd.Compound(children=parts, label="Halberd_R18_Layout_Base")


if __name__ == "__main__":
    halberd_r18_layout_base()
