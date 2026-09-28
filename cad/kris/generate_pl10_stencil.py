"""Stencil-guided PL-10 exterior art revision; original model remains untouched.

Approximate millimeters, aft face Z=0, nose +Z. Broadside attachment landmarks
guide relative stations; the camera is oblique, not a dimensioned side drawing.
No functional internal construction. See pl10_stencil_landmarks.json for trace
provenance and uncertainty; tail notches are informed by the rear attachment.
"""

from cadgen import build123d as bd
from cadgen import report, srgb, step

from generate_pl10 import beveled_plate, cylinder, fastener


LENGTH = 2870.0
BODY_RADIUS = 72.5
BODY_REAR_Z = 8.0
TVC_REAR_Z = BODY_REAR_Z - (BODY_RADIUS * 2) / 4
TVC_FRONT_Z = TVC_REAR_Z + 20.0
AXIAL_IMAGE_START = 34.0
AXIAL_IMAGE_END = 480.0
AZIMUTHS = (0, 90, 180, 270)
BODY_COLOR = srgb("#D0D0C9")
HARDWARE_COLOR = srgb("#8E9797")
DARK_COLOR = srgb("#33383A")
WINDOW_COLOR = srgb("#17262D")
STRAKE_RADIUS = 112.0
TAIL_RADIUS = 232.0
FORWARD_BLADE_RADIUS = BODY_RADIUS + 50.0 / 3.0
WINDOW_RADIUS = 59.0 * 0.93
NOSE_HOUSING_LENGTH_SCALE = 1.3
# Latest user outline supersedes the earlier verbal notch approximation.
# Manual pixel trace: left is noseward, bottom is the body; square the 1px skew.
TAIL_OUTLINE_PIXELS = ((126, 62), (206, 62), (206, 90), (235, 90), (226, 171), (156, 171))
TAIL_OUTLINE_SCALE = (TAIL_RADIUS - (BODY_RADIUS - 1)) / (171 - 62)


def station(image_x):
    return (image_x - AXIAL_IMAGE_START) / (AXIAL_IMAGE_END - AXIAL_IMAGE_START) * LENGTH


def patch(z0, z1, width, height=0.8):
    shell = cylinder(z0, z1, BODY_RADIUS + height) - cylinder(z0 - 1, z1 + 1, BODY_RADIUS - 0.4)
    return shell & bd.Box(20, width, z1 - z0).translate((BODY_RADIUS, 0, (z0 + z1) / 2))


def root_strip(z0, z1, width=10, height=2):
    sections = []
    for z, h in ((z0, 0.5), (z0 + 15, height), (z1 - 15, height), (z1, 0.5)):
        sections.append(bd.Wire.make_polygon([
            (BODY_RADIUS - 1, -width / 2, z),
            (BODY_RADIUS + h, -width / 3, z),
            (BODY_RADIUS + h, width / 3, z),
            (BODY_RADIUS - 1, width / 2, z),
        ], close=True))
    return bd.Solid.make_loft(sections, ruled=True)


def tail_mount_fairing(fin):
    sections = []
    for z, height, half_width in ((TVC_FRONT_Z, 14, 26), (12, 16, 28), (135, 16, 28), (200, 3, 22), (220, 0.6, 12)):
        top, base = BODY_RADIUS + height, BODY_RADIUS - 4
        sections.append(bd.Wire.make_polygon([
            (base, -half_width, z), (top - 3, -half_width, z),
            (top, -half_width + 8, z), (top, half_width - 8, z),
            (top - 3, half_width, z), (base, half_width, z),
        ], close=True))
    fairing = bd.Solid.make_loft(sections, ruled=True)
    fairing -= cylinder(TVC_FRONT_Z - 1, 221, BODY_RADIUS - 0.6)
    # A visible root slot, not a working bearing/actuator interface.
    return fairing - fin.scale((1, 1.4, 1))


@step(out="PL-10_Stencil_Revision.step")
def pl10_stencil():
    parts = []

    def add(shape, name, color=BODY_COLOR, angle=0):
        shape = shape.rotate(bd.Axis.Z, angle)
        shape.label = name
        shape.color = color
        shape.cad_material = {"roughness": 0.65, "metalness": 0.1}
        parts.append(shape)

    report("body proportions and reference-based seams")
    joint_z = [station(x) for x in (73, 106, 311, 343, 458)]
    body_start, seam_width = 42.0, 1.1
    # Extend the housing aft without moving the nose tip or forward blades.
    joint_z[-1] = 2836 - (2836 - (joint_z[-1] + seam_width)) * NOSE_HOUSING_LENGTH_SCALE - seam_width
    for i, end in enumerate(joint_z):
        add(cylinder(body_start, end, BODY_RADIUS), f"body_section_{i + 1}")
        add(cylinder(end, end + seam_width, BODY_RADIUS - 0.2), f"fine_section_joint_{i + 1}", HARDWARE_COLOR)
        body_start = end + seam_width

    report("nose housing and window")
    nose = bd.loft([
        bd.Circle(r).translate((0, 0, z)) for z, r in (
            (body_start, BODY_RADIUS),
            ((body_start + 2836) / 2, (BODY_RADIUS + WINDOW_RADIUS) / 2 + 2),
            (2836, WINDOW_RADIUS)
        )
    ], ruled=False)
    add(nose, "rounded_nose_housing")
    add(cylinder(2836, 2840, WINDOW_RADIUS), "nose_window_rim", HARDWARE_COLOR)
    cap_height, cap_radius = 30.0, WINDOW_RADIUS
    sphere_radius = (cap_radius ** 2 + cap_height ** 2) / (2 * cap_height)
    cap = bd.Sphere(sphere_radius).translate((0, 0, LENGTH - sphere_radius))
    add(cap & cylinder(2840, LENGTH + 1, WINDOW_RADIUS + 1), "dark_nose_window", WINDOW_COLOR)
    parts[-1].cad_material = {"roughness": 0.22, "metalness": 0.1, "clearcoat": 1.0}

    report("seeker housing collars and curved service detail")
    collar = cylinder(body_start - 5, body_start, BODY_RADIUS + 0.6)
    collar -= cylinder(body_start - 6, body_start + 1, BODY_RADIUS - 0.2)
    add(collar, "seeker_base_collar", HARDWARE_COLOR)
    # Conformal overlays come from the actual tapered housing, not a cylinder.
    nose_skin = nose.scale((1.005, 1.005, 1)) - nose
    panel_skin = nose.scale((1.0025, 1.0025, 1)) - nose
    add(nose_skin & cylinder(body_start + 8, body_start + 10, BODY_RADIUS + 1),
        "seeker_collar_seam", HARDWARE_COLOR)
    for i, angle in enumerate(AZIMUTHS, 1):
        panel_z = body_start + 60
        mask = bd.Box(36, 18, 46).translate((BODY_RADIUS - 7, 0, panel_z))
        inset = bd.Box(38, 15.5, 43.5).translate((BODY_RADIUS - 7, 0, panel_z))
        add(nose_skin & (mask - inset), f"seeker_panel_border_{i}", HARDWARE_COLOR, angle)
        add(panel_skin & inset, f"seeker_panel_{i}", angle=angle)
        for j, z in enumerate((body_start + 26, body_start + 94), 1):
            radius = (nose & cylinder(z - 0.005, z + 0.005, BODY_RADIUS + 1)).bounding_box().max.X
            add(fastener(z, radius - 0.2, 1.4), f"seeker_housing_fastener_{i}_{j}", HARDWARE_COLOR, angle)
    bezel = cylinder(2836.3, 2839.3, WINDOW_RADIUS + 0.6)
    bezel -= cylinder(2836, 2840, WINDOW_RADIUS - 0.1)
    add(bezel, "seeker_window_retaining_band", HARDWARE_COLOR)
    for i, angle in enumerate(range(0, 360, 45), 1):
        add(fastener(2837.7, WINDOW_RADIUS + 0.45, 0.65), f"seeker_bezel_fastener_{i}", HARDWARE_COLOR, angle)

    report("shortened strakes and forward surface blades")
    strake = beveled_plate([
        (BODY_RADIUS - 1, station(144)),
        (STRAKE_RADIUS, station(144)),
        (STRAKE_RADIUS, station(277)),
        (BODY_RADIUS - 1, station(285)),
    ], thickness=3.8, bevel=0.65)
    forward = beveled_plate([
        (BODY_RADIUS - 1, station(417)),
        (FORWARD_BLADE_RADIUS, station(418)),
        (FORWARD_BLADE_RADIUS, station(441)),
        (BODY_RADIUS - 1, station(448)),
    ], thickness=3.0, bevel=0.5)
    for i, angle in enumerate(AZIMUTHS, 1):
        add(strake, f"central_strake_{i}", angle=angle)
        add(root_strip(station(143), station(286)), f"central_strake_root_{i}", angle=angle)
        add(forward, f"short_forward_blade_{i}", angle=angle + 45)
        shoe = root_strip(station(417), station(448), 9, 1.5) - forward.scale((1, 1.35, 1))
        add(shoe, f"front_fin_root_shoe_{i}", HARDWARE_COLOR, angle + 45)
        for j, x in enumerate((153, 195, 265), 1):
            z = station(x)
            # Paired small shoes grip the visible strake root on each side.
            for side, suffix in ((-1, "left"), (1, "right")):
                shoe = bd.Box(12, 4.4, 14).translate((BODY_RADIUS + 5, side * 4, z))
                add(shoe, f"strake_attachment_{i}_{j}_{suffix}", HARDWARE_COLOR, angle)
                bolt = fastener(z, BODY_RADIUS + 10.7, 1.4).translate((0, side * 4, 0))
                add(bolt, f"strake_attachment_bolt_{i}_{j}_{suffix}", HARDWARE_COLOR, angle)

    report("stepped tail plates and exterior root covers")
    tail_points = [
        (BODY_RADIUS - 1 + (171 - y) * TAIL_OUTLINE_SCALE,
         (235 - x) * TAIL_OUTLINE_SCALE)
        for x, y in TAIL_OUTLINE_PIXELS
    ]
    tail = beveled_plate(tail_points, thickness=4.5, bevel=0.7)
    fairing = tail_mount_fairing(tail)
    for i, angle in enumerate(AZIMUTHS, 1):
        add(tail, f"stepped_tail_fin_{i}", angle=angle)
        add(fairing, f"tail_mount_fairing_{i}", angle=angle)
        for side, suffix in ((-1, "left"), (1, "right")):
            cheek = cylinder(0, 2, 5).rotate(bd.Axis.X, -90 * side)
            cheek = cheek.translate((BODY_RADIUS + 8, side * 27, 82))
            add(cheek, f"tail_mount_cheek_{i}_{suffix}", DARK_COLOR, angle)
            for j, z in enumerate((30, 110), 1):
                bolt = fastener(z, BODY_RADIUS + 15.7, 1.7).translate((0, side * 16, 0))
                add(bolt, f"tail_mount_bolt_{i}_{suffix}_{j}", HARDWARE_COLOR, angle)

    report("restrained surface detail")
    # Suspension fittings remain on one face; service detailing spans all quadrants.
    near_side = 217.0
    for i, x in enumerate((183, 313), 1):
        z = station(x)
        add(patch(z - 22, z + 22, 18, 1.2), f"visible_fitting_base_{i}", HARDWARE_COLOR, near_side)
        fitting = bd.Box(6, 12, 26).translate((BODY_RADIUS + 3, 0, z))
        fitting -= bd.Box(3, 4, 12).translate((BODY_RADIUS + 5, 0, z))
        add(fitting, f"visible_fitting_cap_{i}", HARDWARE_COLOR, near_side)
        for j, fastener_z in enumerate((z - 17, z + 17), 1):
            add(fastener(fastener_z, BODY_RADIUS + 1.1, 1.6), f"visible_fitting_fastener_{i}_{j}", HARDWARE_COLOR, near_side)
    panel_border = patch(station(404.5), station(413.5), 21, 0.9)
    panel_border -= patch(station(405), station(413), 18, 1.2)
    add(panel_border, "near_side_panel_border", HARDWARE_COLOR, near_side)
    add(patch(station(405), station(413), 18, 0.5), "near_side_dark_panel", DARK_COLOR, near_side)
    for i, angle in enumerate((near_side - 60, near_side + 60), 1):
        for j, x in enumerate((361, 369), 1):
            add(patch(station(x), station(x + 3), 18, 0.3), f"paired_surface_mark_{i}_{j}", DARK_COLOR, angle)
    # Curved cosmetic covers follow the skin rather than floating flat discs.
    hatch_z = station(103)
    hatch_tool = cylinder(-2, 20, 11.2).rotate(bd.Axis.Y, 90).translate((BODY_RADIUS - 2, 0, hatch_z))
    ring_tool = cylinder(-2, 20, 13).rotate(bd.Axis.Y, 90).translate((BODY_RADIUS - 2, 0, hatch_z))
    hatch = hatch_tool & patch(hatch_z - 14, hatch_z + 14, 28, 0.45)
    hatch_ring = (ring_tool - hatch_tool) & patch(hatch_z - 14, hatch_z + 14, 28, 0.8)
    add(hatch, "aft_round_panel", HARDWARE_COLOR, near_side)
    add(hatch_ring, "aft_round_panel_outline", DARK_COLOR, near_side)

    report("reference-render surface covers and rail detail")
    # Approximate visible relief only: no lettering, paint wear, or hidden fittings.
    for name, z0, z1, width, angle in (
        ("aft_access_cover", station(117), station(134), 24, near_side),
        ("forward_access_cover", station(379), station(400), 12, near_side + 8),
    ):
        border = patch(z0, z1, width, 0.75) - patch(z0 + 1.2, z1 - 1.2, width - 2.4, 1.0)
        add(border, f"{name}_border", HARDWARE_COLOR, angle)
        add(patch(z0 + 1.2, z1 - 1.2, width - 2.4, 0.4), name, angle=angle)
        for i, z in enumerate((z0 + 5, z1 - 5), 1):
            add(fastener(z, BODY_RADIUS + 0.4, 1.5), f"{name}_fastener_{i}", HARDWARE_COLOR, angle)
    add(root_strip(station(134), station(282), 8, 2.6), "longitudinal_surface_cover", angle=near_side + 30)
    for i, z in enumerate((station(138), station(278)), 1):
        add(patch(z - 4, z + 4, 12, 3.0), f"longitudinal_cover_end_band_{i}", HARDWARE_COLOR, near_side + 30)

    report("full-circumference service detail")
    # Visible feature families are continued around the body; obscured placements
    # are artistic approximations, not a claim of exact real-world panel layout.
    for quadrant, angle in enumerate((37, 127, 217, 307), 1):
        for j, (x0, x1, width) in enumerate(((83, 95, 20), (290, 302, 16), (384, 399, 12)), 1):
            # Preserve the existing near-side forward cover instead of doubling it.
            if quadrant == 3 and j == 3:
                continue
            z0, z1 = station(x0), station(x1)
            border = patch(z0, z1, width, 0.7) - patch(z0 + 1, z1 - 1, width - 2, 1)
            add(border, f"quadrant_panel_border_{quadrant}_{j}", HARDWARE_COLOR, angle)
            add(patch(z0 + 1, z1 - 1, width - 2, 0.35), f"quadrant_panel_{quadrant}_{j}", angle=angle)
            for k, z in enumerate((z0 + 5, z1 - 5), 1):
                add(fastener(z, BODY_RADIUS + 0.3, 1.4), f"quadrant_panel_bolt_{quadrant}_{j}_{k}", HARDWARE_COLOR, angle)
        for j, z in enumerate((station(73) - 8, station(106) + 8, station(343) + 8), 1):
            add(fastener(z, BODY_RADIUS - 0.1, 1.5), f"quadrant_joint_fastener_{quadrant}_{j}", HARDWARE_COLOR, angle + 17)
    add(hatch, "opposite_aft_round_panel", HARDWARE_COLOR, near_side + 180)
    add(hatch_ring, "opposite_aft_round_panel_outline", DARK_COLOR, near_side + 180)
    add(root_strip(station(134), station(282), 8, 2.6), "opposite_longitudinal_surface_cover", angle=near_side + 210)
    for i, z in enumerate((station(138), station(278)), 1):
        add(patch(z - 4, z + 4, 12, 3), f"opposite_longitudinal_cover_end_band_{i}", HARDWARE_COLOR, near_side + 210)

    report("forward section service panels on all four faces")
    for i, angle in enumerate(AZIMUTHS, 1):
        for j, (z0, z1, width) in enumerate(((2200, 2290, 20), (2520, 2590, 14)), 1):
            border = patch(z0, z1, width, 0.8) - patch(z0 + 1.2, z1 - 1.2, width - 2.4, 1.1)
            add(border, f"front_service_border_{i}_{j}", HARDWARE_COLOR, angle)
            add(patch(z0 + 1.2, z1 - 1.2, width - 2.4, 0.35), f"front_service_panel_{i}_{j}", angle=angle)
            for k, z in enumerate((z0 + 6, z1 - 6), 1):
                add(fastener(z, BODY_RADIUS + 0.3, 1.4), f"front_service_fastener_{i}_{j}_{k}", HARDWARE_COLOR, angle)
        for j, z in enumerate((2384, 2424), 1):
            add(fastener(z, BODY_RADIUS - 0.1, 1.4), f"front_joint_fastener_{i}_{j}", HARDWARE_COLOR, angle + 20)
    for i, z in enumerate((2380, 2420), 1):
        band = cylinder(z, z + 1.3, BODY_RADIUS + 0.2) - cylinder(z - 1, z + 2, BODY_RADIUS - 0.2)
        add(band, f"front_section_seam_{i}", HARDWARE_COLOR)

    report("static aft vane housings and visible vane plates")
    aft = cylinder(BODY_REAR_Z, 42, BODY_RADIUS) - cylinder(BODY_REAR_Z - 1, 26, 60)
    add(aft, "aft_end_cover", HARDWARE_COLOR)
    for i, (z0, z1) in enumerate(((8, 11), (38, 42)), 1):
        rim = cylinder(z0, z1, BODY_RADIUS + 0.6) - cylinder(z0 - 1, z1 + 1, BODY_RADIUS - 0.4)
        add(rim, f"aft_collar_edge_rim_{i}", HARDWARE_COLOR)
    add(cylinder(25.8, 26.2, 59.8), "aft_dark_recess", DARK_COLOR)
    vane_mount = beveled_plate([
        (58, 3), (BODY_RADIUS + 13, 3), (BODY_RADIUS + 16, 7),
        (BODY_RADIUS + 16, 23), (65, 23), (58, 16),
    ], thickness=52, bevel=4).translate((0, 0, TVC_REAR_Z - 3))
    # Matching pockets provide touching seats with no intersecting root volume.
    vane = beveled_plate([(12, 7), (63, 7), (63, 20), (25, 17)], thickness=1.4, bevel=0.2)
    vane = vane.translate((0, 0, TVC_REAR_Z - 3))
    vane_mount -= vane
    for i, angle in enumerate(AZIMUTHS, 1):
        add(vane_mount, f"tvc_exterior_mount_{i}", HARDWARE_COLOR, angle)
        add(vane, f"tvc_static_vane_{i}", DARK_COLOR, angle)

    model = bd.Compound(children=parts, label="PL10_Stencil_Guided_Exterior")
    bounds = model.bounding_box()
    if abs(bounds.max.Z - LENGTH) > 0.01 or abs(bounds.min.Z - TVC_REAR_Z) > 0.01:
        raise ValueError("Unexpected body tip or extended aft envelope")
    if len({p.label for p in parts}) != len(parts):
        raise ValueError("Duplicate part labels")
    return model


if __name__ == "__main__":
    pl10_stencil()
