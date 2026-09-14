"""Check the tail-only hybrid against both original CAD artifacts."""

import math
from pathlib import Path

from cadgen import build123d as bd, read_step
from PIL import Image, ImageDraw


def volume(shape):
    return sum(s.volume for s in shape.solids()) if shape is not None else 0.0


def check_hex_fin_prototype(fin):
    scale = 72.5 / 93.5
    root, old_tip = 105 * scale, math.sqrt(263 ** 2 - 21 ** 2) * scale
    image_scale = (old_tip - root) / 662
    old_neck = root + 51 * image_scale
    neck = 76.6 + (old_neck - 76.6) / 2
    tip = neck + (old_tip - old_neck) * 1.25
    shoulder = neck + 99 * image_scale * 1.25
    neck_half_width = 32 * 95 / 225
    points = [(neck, -neck_half_width), (shoulder, -200 * image_scale * 1.5),
              (tip, -89 * image_scale * 1.5), (tip, 89 * image_scale * 1.5),
              (shoulder, 200 * image_scale * 1.5), (neck, neck_half_width)]
    depth, z_center = 45 * scale, 158 * scale
    # Shoulder and tip corners stay sharp; the foot and neck corners are rounded.
    for radius, y in points[1:5] + [(75.6, 0)]:
        z = z_center - depth / 2 - math.tan(math.radians(18)) * (radius - root)
        assert fin.distance_to(bd.Vertex(radius, y, z)) < 1e-5
        assert fin.distance_to(bd.Vertex(radius, y, z + depth)) < 1e-5
    foot_mask = bd.Box(neck - 75.59, 200, 200, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    foot_mask = foot_mask.translate(((75.59 + neck) / 2, 0, 0))
    assert abs((fin & foot_mask).bounding_box().size.Y - 32) < 0.001, "Finished foot width is not 32 mm"
    assert abs(fin.bounding_box().min.X - 75.6) < 1e-5, "Cylindrical hinge remains or foot is misplaced"
    assert abs(fin.bounding_box().max.X - tip) < 1e-5
    assert abs(fin.bounding_box().size.Y - 400 * image_scale * 1.5) < 1e-5
    for radius in (neck + 3.5, tip - 3.5):
        z = z_center - depth / 2 - math.tan(math.radians(18)) * (radius - root)
        assert fin.distance_to(bd.Vertex(radius, 0, z)) < 1e-5, "Frame wall is not 3.5 mm"
    fillet_radii = []
    for edge in fin.edges():
        a, b, c = (edge.position_at(t) for t in (0, 0.5, 1))
        if max(a.X, b.X, c.X) > neck + 10:
            continue
        cross = (b.X - a.X) * (c.Y - a.Y) - (b.Y - a.Y) * (c.X - a.X)
        if abs(cross) < 1e-6:
            continue
        ab = math.hypot(a.X - b.X, a.Y - b.Y)
        bc = math.hypot(b.X - c.X, b.Y - c.Y)
        ca = math.hypot(c.X - a.X, c.Y - a.Y)
        radius = ab * bc * ca / (2 * abs(cross))
        if abs(radius - 3.0) < 0.001:
            fillet_radii.append(radius)
    assert len(fillet_radii) >= 8, "Four aggressive foot fillets are missing from the top/bottom outlines"
    assert len(fin.solids()) == 1

    # Verify regular hex openings and the actual 2 mm shared material between
    # neighboring cells in two different wall orientations.
    pitch = 28.75
    column_pitch = 1.5 * pitch / math.sqrt(3)
    origin = (neck + tip) / 2 + 0.5625 * column_pitch
    center_y = pitch / 2
    hole_radius = 26.75 / math.sqrt(3)
    for k in range(6):
        x = origin + hole_radius * math.cos(math.radians(60 * k))
        y = center_y + hole_radius * math.sin(math.radians(60 * k))
        z = z_center - math.tan(math.radians(18)) * (x - root)
        assert fin.distance_to(bd.Vertex(x, y, z)) < 1e-5
    centers_checked = 0
    for column in range(-6, 7):
        x = origin + column * column_pitch
        for row in range(-5, 6):
            y = (row + 0.5) * pitch + (column % 2) * pitch / 2
            distances = [((b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])) /
                         math.hypot(b[0] - a[0], b[1] - a[1])
                         for a, b in zip(points, points[1:] + points[:1])]
            if min(distances) > 3.75:
                ray = bd.Axis((x, y, 0), (0, 0, 1))
                assert not any(shell.find_intersection_points(ray) for shell in fin.shells()), (column, row)
                centers_checked += 1
    assert centers_checked >= 6
    top_face = max(fin.faces(), key=lambda face: len(face.inner_wires()))
    holes = top_face.inner_wires()
    assert len(holes) == 19, "Unexpected honeycomb cell count"
    full_cell_area = 26.75 ** 2 * math.sqrt(3) / 2
    fractions = [bd.Face(wire).area * math.cos(math.radians(18)) / full_cell_area for wire in holes]
    assert min(fractions) > 0.18, "A small clipped cell remains"
    assert max(fractions) < 1.00001
    assert sum(fraction > 0.999 for fraction in fractions) == 6
    for mx, my, nx, ny in ((origin, 0, 0, 1),
                          (origin + column_pitch / 2, pitch / 4, math.sqrt(3) / 2, -0.5)):
        z = z_center - math.tan(math.radians(18)) * (mx - root)
        ray = bd.Axis((mx, my, z), (nx, ny, 0))
        hits = [point for shell in fin.shells() for point, _normal in shell.find_intersection_points(ray)]
        distances = [(point.X - mx) * nx + (point.Y - my) * ny for point in hits]
        assert any(abs(value - 1) < 1e-5 for value in distances)
        assert any(abs(value + 1) < 1e-5 for value in distances)
        assert not any(abs(value) < 0.99 for value in distances)
        probe = bd.Box(0.1, 0.1, 0.1).translate((mx, my, z))
        assert volume(fin & probe) > 0.00099


def main():
    folder = Path(__file__).resolve().parent
    source = {p.label: p for p in read_step(folder / "PL-10_Stencil_Revision.step").children}
    hybrid = read_step(folder / "IRM-S4_Kris_PL10_Hybrid.step")
    parts = {p.label: p for p in hybrid.children}
    removed = ("stepped_tail_fin_", "tail_mount_", "tvc_exterior_mount_", "tvc_static_vane_")
    retained = {name: part for name, part in source.items()
                if not name.startswith(removed) and name != "body_section_1"}
    assert not any(name.startswith(("stepped_tail_fin_", "tail_mount_")) for name in parts)
    for name, old in retained.items():
        current = parts[name]
        assert abs(current.volume - old.volume) < max(1e-5, old.volume * 1e-8), name
        assert (current.bounding_box().min - old.bounding_box().min).length < 1e-5, name
        assert (current.bounding_box().max - old.bounding_box().max).length < 1e-5, name

    reference_grid = parts["kris_grid_fin_2"].rotate(bd.Axis.Z, -90)
    def section(shape, z):
        slab = bd.Box(1000, 1000, 1, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).translate((0, 0, z))
        return (shape & slab).translate((0, 0, -z))
    inner_wall_mask = bd.Box(100, 200, 3).translate((121.9, 0, 0.5))
    reference_section = section(source["tvc_exterior_mount_1"], -19) & inner_wall_mask
    triangle = ((36.9, -9.25), (71.9, -9.25), (71.9, 25.75))
    def cross(a, b, p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    for i in range(1, 5):
        print(f"Checking mounting station {i}...", flush=True)
        offset = -11.9
        grid = parts[f"kris_grid_fin_{i}"]
        local = grid.rotate(bd.Axis.Z, -(i - 1) * 90)
        tolerance = max(1e-5, reference_grid.volume * 1e-8)
        check_hex_fin_prototype(local)
        assert volume(local - reference_grid) < tolerance
        assert volume(reference_grid - local) < tolerance
        housing = parts[f"grid_fin_housing_{i}"]
        support = parts[f"grid_tvc_support_{i}"]
        local_housing = housing.rotate(bd.Axis.Z, -(i - 1) * 90)
        local_support = support.rotate(bd.Axis.Z, -(i - 1) * 90)
        local_housing = local_housing.translate((-offset, 0, 0))
        local_support = local_support.translate((-offset, 0, 0))
        assert abs(local_housing.bounding_box().size.Y - 52) < 1e-5
        assert abs(local_housing.bounding_box().size.Z - 140) < 1e-5
        for sample in (section(local_housing, 160), section(local_support, 40)):
            assert volume(sample - reference_section) < 1e-5
            assert volume(reference_section - sample) < 1e-5
        mount = parts[f"tvc_exterior_mount_{i}"]
        local_mount = mount.rotate(bd.Axis.Z, -(i - 1) * 90).translate((-offset, 0, 0))
        assert abs(local_mount.bounding_box().min.X - 71.9) < 1e-5
        assert abs(local_mount.bounding_box().max.X - 88.5) < 1e-5
        assert abs(local_mount.bounding_box().size.Y - 52) < 1e-5
        assert abs(local_mount.bounding_box().min.Z + 28.25) < 1e-5
        assert abs(local_mount.bounding_box().max.Z + 8.25) < 1e-5
        for x, z in ((71.9, -19.25), (77.9, -28.25)):
            assert any(abs(v.X - x) < 1e-5 and abs(v.Z - z) < 1e-5 for v in local_mount.vertices())
        vane = parts[f"tvc_static_vane_{i}"]
        local_vane = vane.rotate(bd.Axis.Z, -(i - 1) * 90).translate((-offset, 0, 0))
        vane_vertices = local_vane.vertices()
        for x, z in triangle:
            assert local_vane.distance_to(bd.Vertex(x, 0, z)) < 1e-5
        assert abs(local_vane.bounding_box().size.X - 35) < 1e-5
        assert abs(local_vane.bounding_box().size.Z - 35) < 1e-5
        assert abs(local_vane.bounding_box().min.Z + 9.25) < 1e-5
        for v in vane_vertices:
            assert all(cross(triangle[j], triangle[(j + 1) % 3], (v.X, v.Z)) >= -1e-5 for j in range(3))
        assert vane.distance_to(mount) < 1e-5
        assert vane.distance_to(support) < 1e-5
        boss = parts[f"tvc_vane_mount_{i}"]
        local_boss = boss.rotate(bd.Axis.Z, -(i - 1) * 90)
        boss_bounds = local_boss.bounding_box()
        assert abs(boss_bounds.min.X - 59.5) < 1e-5
        assert abs(boss_bounds.max.X - 60) < 1e-5
        assert abs(boss_bounds.size.Y - 7) < 1e-5
        assert abs(boss_bounds.size.Z - 7) < 1e-5
        assert abs((boss_bounds.min.Z + boss_bounds.max.Z) / 2 - 8.25) < 1e-5
        circles = [edge for edge in local_boss.edges() if edge.geom_type == bd.GeomType.CIRCLE
                   and abs(edge.radius - 3.5) < 1e-5 and abs(edge.arc_center.X - 59.5) < 1e-5]
        assert circles
        assert boss.distance_to(vane) < 1e-5
        assert boss.distance_to(support) < 1e-5
        assert volume(housing & grid) < 1e-5
        assert housing.distance_to(grid) < 1e-5
        assert support.distance_to(housing) < 1e-5
        assert support.distance_to(parts[f"tvc_exterior_mount_{i}"]) < 1e-5
        assert volume(housing & parts["body_section_1"]) < 1e-5
        assert housing.distance_to(parts["body_section_1"]) < 1e-5
        for j in (1, 2):
            assert f"grid_hinge_cover_{i}_{j}" not in parts
        for j in range(i + 1, 5):
            assert grid.distance_to(parts[f"kris_grid_fin_{j}"]) > 0.1

        # Sample the visible roof's inward-curving return to the body cylinder.
        world_local_housing = local_housing.translate((offset, 0, 0))
        radii = []
        for z in (165.01, 171, 180, 195, 210, 219, 224.999):
            ray = bd.Axis((-100, 0, z), (1, 0, 0))
            intersections = [point for shell in world_local_housing.shells()
                             for point, _normal in shell.find_intersection_points(ray)]
            assert intersections, (i, z)
            radii.append(max(point.X for point in intersections))
        assert all(a + 0.01 >= b for a, b in zip(radii, radii[1:])), radii
        assert abs(radii[0] - 76.6) < 0.02
        assert abs(radii[3] - 73.525) < 0.02
        assert abs(radii[-1] - 72.5) < 0.01
        assert radii[3] < (radii[0] + radii[-1]) / 2
        transverse = bd.Axis((68.5, -100, 195), (0, 1, 0))
        points = [point for shell in world_local_housing.shells()
                  for point, _normal in shell.find_intersection_points(transverse)]
        assert len(points) >= 2
        width = max(point.Y for point in points) - min(point.Y for point in points)
        assert abs(width - 52 * (0.75 ** 0.5)) < 0.05, (i, width)
        reference_housing = parts["grid_fin_housing_1"].translate((11.9, 0, 0))
        assert volume(local_housing - reference_housing) < 1e-5
        assert volume(reference_housing - local_housing) < 1e-5

    original_body, trimmed_body = source["body_section_1"], parts["body_section_1"]
    assert len(trimmed_body.solids()) == 1
    assert (trimmed_body.bounding_box().min - original_body.bounding_box().min).length < 1e-5
    assert (trimmed_body.bounding_box().max - original_body.bounding_box().max).length < 1e-5
    housings = [parts[f"grid_fin_housing_{i}"] for i in range(1, 5)]
    removed_volume = sum(volume(original_body & housing) for housing in housings)
    # Only negligible disconnected boolean flakes may be removed in addition.
    assert abs(original_body.volume - trimmed_body.volume - removed_volume) <= original_body.volume * 1e-6
    assert volume(trimmed_body - original_body) < 1e-5

    bore_edges = [edge for edge in parts["aft_end_cover"].edges()
                  if edge.geom_type == bd.GeomType.CIRCLE and abs(edge.radius - 60) < 1e-5]
    assert bore_edges
    for i in range(1, 5):
        for prefix in ("grid_fin_housing_", "grid_tvc_support_", "tvc_exterior_mount_"):
            local_wall = parts[f"{prefix}{i}"].rotate(bd.Axis.Z, -(i - 1) * 90)
            assert abs(local_wall.bounding_box().min.X - bore_edges[0].radius) < 1e-5
            tangent_faces = [face for face in local_wall.faces() if face.geom_type == bd.GeomType.PLANE
                             and abs(abs(face.normal_at().X) - 1) < 1e-5
                             and abs(face.center().X - bore_edges[0].radius) < 1e-5]
            assert tangent_faces, (prefix, i)

    bounds = {name: p.bounding_box() for name, p in parts.items()}
    for name, part in parts.items():
        if not name.startswith(("tvc_exterior_mount_", "tvc_static_vane_", "tvc_vane_mount_")):
            continue
        a = bounds[name]
        for other, b in bounds.items():
            if name == other:
                continue
            if all(getattr(a.min, axis) <= getattr(b.max, axis) and
                   getattr(b.min, axis) <= getattr(a.max, axis) for axis in ("X", "Y", "Z")):
                assert volume(part & parts[other]) < 1e-5, (name, other)
    assert abs(hybrid.bounding_box().max.Z - 2870) < 1e-5
    assert abs(hybrid.bounding_box().min.Z + 28.25) < 1e-5
    print(f"PASS: {len(retained)} non-tail PL-10 parts preserve volume and placement.")
    print("PASS: all four rear fins match the approved hexagonal planform under 90-degree rotations.")
    print("PASS: finished rounded foot is 32 mm wide; frame span, outer width, 3.5 mm rim, and 18-degree cant retained.")
    print("PASS: 19 hexagonal cells, 26.75 mm clear size on 28.75 mm pitch, and 2 mm shared walls.")
    print("PASS: no clipped cell is smaller than 18% of a full hexagon; six complete cells preserved.")
    print("PASS: housing and support cross-sections match the exposed TVC mount outline (52 mm wide).")
    print("PASS: right-triangular vanes contact straight inner walls; mounting blocks have the specified rear chamfer.")
    print("PASS: vanes raised 15 mm toward the nose, with 35 mm equal legs and a 45-degree diagonal.")
    print("PASS: four 7 mm diameter vane bosses project 0.5 mm inward at the wall-edge midpoints, with fitted non-overlapping contacts.")
    print("PASS: all housing roofs return smoothly inward to the body over a 60 mm forward extension.")
    print("PASS: all four housing caps retain the approved rounded profile; the prototype seat fits the replacement foot.")
    print("PASS: complementary body pockets eliminate housing/body volume overlap; connected body and exterior envelope preserved.")
    print("PASS: all four housing/support/mount inner walls are tangent to the 120 mm bore after the 11.9 mm inward offset.")
    print("PASS: grid fins are separated and TVC geometry has no intersecting volume with other parts.")

    # A side-profile diagram of the actual exported solids, in the user's colors.
    image = Image.new("RGB", (600, 600), "white")
    draw = ImageDraw.Draw(image)
    for name, color in (("grid_tvc_support_1", (61, 157, 211)),
                        ("tvc_exterior_mount_1", (61, 157, 211)),
                        ("tvc_static_vane_1", (111, 180, 35)),
                        ("tvc_vane_mount_1", (130, 138, 143))):
        vertices, triangles = parts[name].tessellate(0.05, 0.1)
        points = [(70 + (v.X - 30) * 7, 60 + (35 - v.Z) * 7) for v in vertices]
        for indices in triangles:
            draw.polygon([points[j] for j in indices], fill=color)
    draw.rectangle((0, 0, 600, 45), fill="white")
    draw.text((20, 15), "Exported CAD: blue support, green vane, gray 7 mm boss", fill="black")
    draw.text((20, 565), "Nose upward | radial outward to the right | grid fins omitted", fill="black")
    output = folder / "Kris_hybrid_TVC_profile.png"
    image.save(output)
    print(f"saved {output}")


if __name__ == "__main__":
    main()
