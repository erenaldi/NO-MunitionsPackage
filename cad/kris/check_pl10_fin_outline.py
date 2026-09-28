"""Validate exported fins against the latest manually traced user outline.

Writes a blue-outline/gray-CAD comparison; this is not source-image segmentation.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw
from cadgen import build123d as bd, read_step


def overlap_volume(first, second):
    overlap = first & second
    return sum(solid.volume for solid in overlap.solids()) if overlap is not None else 0.0


def main():
    folder = Path(__file__).resolve().parent
    model = read_step(folder / "PL-10_Stencil_Revision.step")
    parts = {part.label: part for part in model.children}
    outline = ((126, 62), (206, 62), (206, 90), (235, 90), (226, 171), (156, 171))
    root_radius, outer_radius = 71.5, 232.0
    scale = (outer_radius - root_radius) / 109
    expected = [(root_radius + (171 - y) * scale, (235 - x) * scale) for x, y in outline]
    for i in range(4):
        fin = parts[f"stepped_tail_fin_{i + 1}"].rotate(bd.Axis.Z, -90 * i)
        vertices = list(fin.vertices())
        for radius, z in expected:
            assert any(abs(v.X - radius) < 1e-5 and abs(v.Z - z) < 1e-5 for v in vertices), (i, radius, z)
        assert abs(fin.bounding_box().size.Z - 160.5) < 1e-5
        assert abs(fin.bounding_box().size.X - 160.5) < 1e-5
        forward = parts[f"short_forward_blade_{i + 1}"].rotate(bd.Axis.Z, -(45 + 90 * i))
        assert abs(forward.bounding_box().max.X - (72.5 + 50 / 3)) < 1e-5
        assert abs(forward.bounding_box().size.Y - 3) < 1e-5
    assert abs(parts["body_section_1"].bounding_box().size.X - 145) < 1e-5
    assert abs(parts["dark_nose_window"].bounding_box().size.X - 109.74) < 1e-5
    previous_housing_length = 2836 - ((458 - 34) / 446 * 2870 + 1.1)
    assert abs(parts["rounded_nose_housing"].bounding_box().size.Z - previous_housing_length * 1.3) < 1e-5
    assert abs(model.bounding_box().max.Z - 2870) < 1e-5
    assert abs(model.bounding_box().min.Z - (8 - 145 / 4)) < 1e-5
    assert abs(model.bounding_box().size.Z - 2898.25) < 1e-5

    bounds = {name: part.bounding_box() for name, part in parts.items()}
    for i in range(1, 5):
        fairing = parts[f"tail_mount_fairing_{i}"]
        mount = parts[f"tvc_exterior_mount_{i}"]
        vane = parts[f"tvc_static_vane_{i}"]
        assert overlap_volume(fairing, parts["body_section_1"]) > 0
        assert overlap_volume(fairing, parts["aft_end_cover"]) > 0
        local_fairing = fairing.rotate(bd.Axis.Z, -(i - 1) * 90)
        local_mount = mount.rotate(bd.Axis.Z, -(i - 1) * 90)
        assert abs(local_fairing.bounding_box().size.Y - 56) < 1e-5
        assert abs(local_mount.bounding_box().size.Y - 52) < 1e-5
        assert abs(local_mount.bounding_box().min.Z - (8 - 145 / 4)) < 1e-5
        assert abs(mount.bounding_box().max.Z - (-8.25)) < 1e-5
        assert mount.distance_to(fairing) < 1e-5
        assert overlap_volume(vane, mount) < 1e-5
        assert vane.distance_to(mount) < 1e-5
        # Test every potentially intersecting part, not only the intended seat.
        # Disjoint AABBs prove zero overlap without an expensive boolean.
        for name in (f"tvc_exterior_mount_{i}", f"tvc_static_vane_{i}"):
            a = bounds[name]
            for other, b in bounds.items():
                if other == name:
                    continue
                if all(getattr(a.min, axis) <= getattr(b.max, axis) and
                       getattr(b.min, axis) <= getattr(a.max, axis) for axis in ("X", "Y", "Z")):
                    assert overlap_volume(parts[name], parts[other]) < 1e-5, (name, other)
        assert vane.distance_to(parts["aft_dark_recess"]) > 0.1
        for j in range(1, 5):
            fin = parts[f"stepped_tail_fin_{j}"]
            assert overlap_volume(fin, fairing) < 1e-5
            assert overlap_volume(fin, mount) < 1e-5
            if j > i:
                assert vane.distance_to(parts[f"tvc_static_vane_{j}"]) > 0.1
        assert sum(name.startswith(f"strake_attachment_{i}_") for name in parts) == 6
    for quadrant, expected_angle in enumerate((37, 127, 217, 307), 1):
        panels = [part for name, part in parts.items() if name.startswith(f"quadrant_panel_{quadrant}_")]
        assert len(panels) == (2 if quadrant == 3 else 3)
        for panel in panels:
            center = panel.center()
            angle = math.degrees(math.atan2(center.Y, center.X)) % 360
            assert abs(angle - expected_angle) < 0.01

    for i in range(1, 5):
        assert all(f"front_service_panel_{i}_{j}" in parts for j in (1, 2))
        assert f"seeker_panel_{i}" in parts
        assert f"front_fin_root_shoe_{i}" in parts
        assert overlap_volume(parts[f"front_fin_root_shoe_{i}"], parts[f"short_forward_blade_{i}"]) < 1e-5
    for name, part in parts.items():
        if name.startswith("seeker_"):
            assert part.distance_to(parts["dark_nose_window"]) > 0.01, name

    image = Image.new("RGB", (600, 600), "white")
    draw = ImageDraw.Draw(image)
    project = lambda x, y: (75 + (x - 126) * 4, 85 + (y - 62) * 4)
    vertices, triangles = parts["stepped_tail_fin_1"].tessellate(0.05, 0.1)
    points = [project(235 - v.Z / scale, 171 - (v.X - root_radius) / scale) for v in vertices]
    for triangle in triangles:
        draw.polygon([points[index] for index in triangle], fill=(180, 187, 185))
    trace = [project(x, y) for x, y in outline]
    draw.line(trace + trace[:1], fill=(0, 113, 188), width=3)
    draw.text((30, 20), "BLUE: manual user outline | GRAY: exported CAD", fill="black")
    draw.text((30, 42), "Uniform scale; no independent axial/radial stretching", fill="black")
    draw.text((30, 555), "Nose <---     Lower edge attaches to body", fill="black")
    output = folder / "PL-10_tail_outline_check.png"
    image.save(output)
    print("PASS: all four tail profiles match the uniformly scaled six-corner outline.")
    print("PASS: body/nose proportions and forward-fin span/45-degree offset preserved.")
    print("PASS: doubled mount widths and 36.25 mm aft projection; touching TVC seats without clipping any other part.")
    print("PASS: service panels cover all four quadrants and all strakes have six attachment shoes.")
    print("PASS: four-sided forward/seeker detail; root shoes clear fins and seeker hardware clears the optical window.")
    print(f"saved {output}")


if __name__ == "__main__":
    main()
