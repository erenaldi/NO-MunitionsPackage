"""Inventory the selected saved Kris hybrid, without rebuilding its source."""
from pathlib import Path
from collections import Counter
from cadgen import read_scene

# Conservative surface-detail count: omit main forms, their structural mounts,
# and optical/exhaust back faces. Count placed objects, not unique designs or faces.
PRIMARY_PREFIXES = (
    "body_section_", "central_strake_", "short_forward_blade_",
    "front_fin_root_shoe_", "kris_grid_fin_", "grid_fin_housing_",
    "grid_tvc_support_", "tvc_exterior_mount_", "tvc_static_vane_",
    "tvc_vane_mount_",
)
PRIMARY_NAMES = {"rounded_nose_housing", "dark_nose_window", "aft_dark_recess"}


def category(label):
    if label in PRIMARY_NAMES or label.startswith(PRIMARY_PREFIXES):
        return "Primary forms / structural mounts / optical or recess faces"
    if "fastener" in label or "bolt" in label:
        return "Fasteners"
    if label.startswith("strake_attachment_"):
        return "Small attachment plates"
    if "panel" in label or "cover" in label:
        return "Panels / covers / borders"
    return "Seams / rims / bands / fittings / marks"


if __name__ == "__main__":
    source = Path(__file__).resolve().parents[2] / "kris" / "IRM-S4_Kris_PL10_Hybrid.step"
    scene = read_scene(source)
    leaves = tuple(scene.leaves())
    print(f"Document hash: {scene.document_hash}")
    print(f"Total placed objects: {len(leaves)}")
    counts = Counter(category(leaf.label) for leaf in leaves)
    for name, count in counts.items():
        print(f"{name}: {count}")
    primary = counts["Primary forms / structural mounts / optical or recess faces"]
    print(f"Surface detail objects: {len(leaves) - primary}")
