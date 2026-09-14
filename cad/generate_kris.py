import math

from cadgen import build123d as bd
from cadgen import srgb, step


# R-93M reference dimensions, in millimeters. The exhaust is at Z=0 and the
# seeker tip is at Z=LENGTH. Reference image: R93M_Arc_reference.png.
LENGTH = 2870.0
BODY_RADIUS = 93.5
DEPLOYED_RADIUS = 263.0

NOZZLE_END_Z = 72.0
AFT_COLLAR_END_Z = 118.0
AFT_BODY_SEAM_Z = 865.0
FIRST_BODY_SEAM_Z = 1375.0
SECOND_BODY_SEAM_Z = 1495.0
CONTROL_BAND_START_Z = 2285.0
CONTROL_SECTION_START_Z = 2303.0
SEEKER_COLLAR_START_Z = 2670.0
NOSE_START_Z = 2690.0
SEEKER_BEZEL_START_Z = 2826.0
GLASS_START_Z = 2830.0
GLASS_RADIUS = 40.0

VANE_A_START_Z = 2417.5
VANE_A_END_Z = 2522.5
VANE_A_TIP_RADIUS = (BODY_RADIUS - 1.0) + (145.0 - (BODY_RADIUS - 1.0)) * 1.5
VANE_B_TIP_RADIUS = (
    (BODY_RADIUS - 1.0) + (122.0 - (BODY_RADIUS - 1.0)) * 1.5 * 1.5
)
VANE_B_CENTER_Z = 2590.0
VANE_B_CHORD = VANE_B_TIP_RADIUS - (BODY_RADIUS - 1.0)
VANE_B_START_Z = VANE_B_CENTER_Z - VANE_B_CHORD * 0.5
VANE_B_END_Z = VANE_B_CENTER_Z + VANE_B_CHORD * 0.5
VANE_THICKNESS = 5.0

FAIRING_START_Z = 240.0
FAIRING_END_Z = 1280.0
FAIRING_HEIGHT = 28.0
FAIRING_WIDTH = 7.0

GRID_FIN_Z = 158.0
GRID_FIN_THICKNESS = 45.0
GRID_FIN_ROOT_RADIUS = 105.0
GRID_FIN_INNER_HALF_WIDTH = 49.0
GRID_FIN_OUTER_HALF_WIDTH = 21.0
GRID_FIN_FRAME = 6.0
GRID_FIN_RIB = 3.0
GRID_FIN_CANT_DEGREES = 18.0
GRID_FIN_AZIMUTHS = (45.0, 135.0, 225.0, 315.0)

BODY_COLOR = srgb("#D9DEE1")
METAL_COLOR = srgb("#89949B")
FIN_COLOR = srgb("#252A2D")
SEEKER_COLOR = srgb("#26343B")
NOZZLE_COLOR = srgb("#63372F")


def cylinder_between(z_min, z_max, radius):
    return bd.Cylinder(
        radius,
        z_max - z_min,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    ).translate((0.0, 0.0, z_min), transform=True)


def circle_section(z, radius):
    return bd.Circle(radius).translate((0.0, 0.0, z), transform=True)


def annular_loft(outer_sections, inner_sections):
    outer = bd.loft(
        [circle_section(z, radius) for z, radius in outer_sections], ruled=True
    )
    inner = bd.loft(
        [circle_section(z, radius) for z, radius in inner_sections], ruled=True
    )
    return outer - inner


def make_nozzle():
    return annular_loft(
        [(0.0, 48.0), (48.0, 56.0), (NOZZLE_END_Z, 58.0)],
        [(0.0, 32.0), (NOZZLE_END_Z + 1.0, 40.0)],
    )


def make_aft_collar():
    collar = cylinder_between(NOZZLE_END_Z, AFT_COLLAR_END_Z, 99.0)
    lug = bd.Box(
        18.0,
        24.0,
        AFT_COLLAR_END_Z - NOZZLE_END_Z,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    ).translate((99.0, 0.0, NOZZLE_END_Z), transform=True)
    return collar.fuse(*[lug.rotate(bd.Axis.Z, angle) for angle in range(0, 360, 45)])


def make_seeker_fairing():
    return bd.loft(
        [
            circle_section(NOSE_START_Z, BODY_RADIUS),
            circle_section(2740.0, 88.0),
            circle_section(2790.0, 68.0),
            circle_section(SEEKER_BEZEL_START_Z, 42.0),
        ],
        ruled=False,
    )


def make_ir_dome():
    return bd.loft(
        [
            circle_section(GLASS_START_Z, GLASS_RADIUS),
            circle_section(2840.0, 38.73),
            circle_section(2850.0, 34.64),
            circle_section(2860.0, 26.46),
            circle_section(2866.0, 17.44),
            circle_section(LENGTH, 1.0),
        ],
        ruled=False,
    )


def extrude_xz_profile(points, thickness):
    wire = bd.Wire.make_polygon(
        [(x, -thickness * 0.5, z) for x, z in points], close=True
    )
    return bd.Solid.extrude(bd.Face(wire), (0.0, thickness, 0.0))


def make_control_vane(z_start, z_end, tip_radius, edge_scale=1.0):
    edge_inset = 12.0 * edge_scale
    return extrude_xz_profile(
        [
            (BODY_RADIUS - 1.0, z_start),
            (tip_radius, z_start + edge_inset),
            (tip_radius, z_end - edge_inset),
            (BODY_RADIUS - 1.0, z_end),
        ],
        VANE_THICKNESS,
    )


def make_forward_control_vane():
    root_radius = BODY_RADIUS - 1.0
    return extrude_xz_profile(
        [
            (root_radius, VANE_B_START_Z),
            (VANE_B_TIP_RADIUS, VANE_B_START_Z),
            (root_radius, VANE_B_END_Z),
        ],
        VANE_THICKNESS,
    )


def make_longitudinal_fairing():
    base_radius = BODY_RADIUS - 1.0

    def section(z):
        return bd.Wire.make_polygon(
            [
                (base_radius, -FAIRING_WIDTH * 0.5, z),
                (BODY_RADIUS + FAIRING_HEIGHT, 0.0, z),
                (base_radius, FAIRING_WIDTH * 0.5, z),
            ],
            close=True,
        )

    return bd.Solid.make_loft(
        [
            bd.Vertex(base_radius, 0.0, FAIRING_START_Z),
            section(FAIRING_START_Z + 130.0),
            section(FAIRING_END_Z - 140.0),
            bd.Vertex(base_radius, 0.0, FAIRING_END_Z),
        ],
        ruled=True,
    )


def xy_prism(points, z_min, thickness):
    wire = bd.Wire.make_polygon([(x, y, z_min) for x, y in points], close=True)
    return bd.Solid.extrude(bd.Face(wire), (0.0, 0.0, thickness))


def sheared_xy_prism(points, z_min, thickness, x_origin, z_slope):
    def section(z_offset):
        return bd.Wire.make_polygon(
            [
                (x, y, z_min + z_offset + (x - x_origin) * z_slope)
                for x, y in points
            ],
            close=True,
        )

    return bd.Solid.make_loft([section(0.0), section(thickness)], ruled=True)


def make_faceted_collar():
    points = [
        (
            100.0 * math.cos(math.radians(index * 30.0 + 15.0)),
            100.0 * math.sin(math.radians(index * 30.0 + 15.0)),
        )
        for index in range(12)
    ]
    return xy_prism(points, SEEKER_COLLAR_START_Z, NOSE_START_Z - SEEKER_COLLAR_START_Z)


def xy_bar(start, end, width, z_center, axial_depth=GRID_FIN_THICKNESS):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx))
    bar = bd.Box(
        length,
        width,
        axial_depth,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER),
    )
    return bar.rotate(bd.Axis.Z, angle).translate(
        ((start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5, z_center),
        transform=True,
    )


def sheared_xy_bar(start, end, width, z_center, axial_depth, x_origin, z_slope):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    normal_x = -dy * width * 0.5 / length
    normal_y = dx * width * 0.5 / length
    points = [
        (start[0] + normal_x, start[1] + normal_y),
        (end[0] + normal_x, end[1] + normal_y),
        (end[0] - normal_x, end[1] - normal_y),
        (start[0] - normal_x, start[1] - normal_y),
    ]
    return sheared_xy_prism(
        points,
        z_center - axial_depth * 0.5,
        axial_depth,
        x_origin,
        z_slope,
    )


def make_grid_fin():
    z_min = GRID_FIN_Z - GRID_FIN_THICKNESS * 0.5
    z_slope = -math.tan(math.radians(GRID_FIN_CANT_DEGREES))
    model_tip_radius = math.sqrt(
        DEPLOYED_RADIUS * DEPLOYED_RADIUS
        - GRID_FIN_OUTER_HALF_WIDTH * GRID_FIN_OUTER_HALF_WIDTH
    )

    outer = [
        (GRID_FIN_ROOT_RADIUS, -GRID_FIN_INNER_HALF_WIDTH),
        (model_tip_radius, -GRID_FIN_OUTER_HALF_WIDTH),
        (model_tip_radius, GRID_FIN_OUTER_HALF_WIDTH),
        (GRID_FIN_ROOT_RADIUS, GRID_FIN_INNER_HALF_WIDTH),
    ]
    inner = [
        (GRID_FIN_ROOT_RADIUS + GRID_FIN_FRAME, -GRID_FIN_INNER_HALF_WIDTH + GRID_FIN_FRAME),
        (model_tip_radius - GRID_FIN_FRAME, -GRID_FIN_OUTER_HALF_WIDTH + GRID_FIN_FRAME),
        (model_tip_radius - GRID_FIN_FRAME, GRID_FIN_OUTER_HALF_WIDTH - GRID_FIN_FRAME),
        (GRID_FIN_ROOT_RADIUS + GRID_FIN_FRAME, GRID_FIN_INNER_HALF_WIDTH - GRID_FIN_FRAME),
    ]
    outer_solid = sheared_xy_prism(
        outer, z_min, GRID_FIN_THICKNESS, GRID_FIN_ROOT_RADIUS, z_slope
    )
    inner_solid = sheared_xy_prism(
        inner,
        z_min - 0.5,
        GRID_FIN_THICKNESS + 1.0,
        GRID_FIN_ROOT_RADIUS,
        z_slope,
    )
    frame = outer_solid - inner_solid

    inner_x = GRID_FIN_ROOT_RADIUS + GRID_FIN_FRAME
    outer_x = model_tip_radius - GRID_FIN_FRAME
    inner_half_width = GRID_FIN_INNER_HALF_WIDTH - GRID_FIN_FRAME
    outer_half_width = GRID_FIN_OUTER_HALF_WIDTH - GRID_FIN_FRAME
    def grid_bar(start, end):
        return sheared_xy_bar(
            start,
            end,
            GRID_FIN_RIB,
            GRID_FIN_Z,
            GRID_FIN_THICKNESS,
            GRID_FIN_ROOT_RADIUS,
            z_slope,
        )

    lattice = [
        grid_bar(
            (inner_x, 0.0),
            (outer_x, 0.0),
        )
    ]

    bay_fractions = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    for fraction in bay_fractions[1:-1]:
        x = inner_x + (outer_x - inner_x) * fraction
        half_width = inner_half_width + (
            outer_half_width - inner_half_width
        ) * fraction
        lattice.append(
            grid_bar(
                (x, -half_width),
                (x, half_width),
            )
        )

    for start_fraction, end_fraction in zip(bay_fractions, bay_fractions[1:]):
        start_x = inner_x + (outer_x - inner_x) * start_fraction
        end_x = inner_x + (outer_x - inner_x) * end_fraction
        start_half_width = inner_half_width + (
            outer_half_width - inner_half_width
        ) * start_fraction
        end_half_width = inner_half_width + (
            outer_half_width - inner_half_width
        ) * end_fraction
        lattice.extend(
            [
                grid_bar(
                    (start_x, -start_half_width),
                    (end_x, end_half_width),
                ),
                grid_bar(
                    (start_x, start_half_width),
                    (end_x, -end_half_width),
                ),
            ]
        )

    clipped_lattice = []
    for rib in lattice:
        clipped = rib.intersect(inner_solid)
        if clipped:
            clipped_lattice.extend(clipped)
    panel = frame.fuse(*clipped_lattice)

    hinge = bd.Cylinder(
        12.0,
        GRID_FIN_THICKNESS + 18.0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER),
    ).translate((GRID_FIN_ROOT_RADIUS, 0.0, GRID_FIN_Z), transform=True)
    return panel.fuse(hinge)


def styled_part(prototype, angle, label, color, material=None):
    part = prototype.rotate(bd.Axis.Z, angle)
    part.label = label
    part.color = color
    if material is not None:
        part.cad_material = material
    return part


def style_body_part(part, label, color=BODY_COLOR, metalness=0.15):
    part.label = label
    part.color = color
    part.cad_material = {"roughness": 0.65, "metalness": metalness}
    return part


@step(out="IRM-S4_Kris.step")
def kris():
    nozzle = style_body_part(make_nozzle(), "exhaust_nozzle", NOZZLE_COLOR, 0.65)
    nozzle.cad_material["roughness"] = 0.45
    aft_collar = style_body_part(make_aft_collar(), "aft_motor_collar", METAL_COLOR, 0.5)

    aft_motor = style_body_part(
        cylinder_between(AFT_COLLAR_END_Z, AFT_BODY_SEAM_Z, BODY_RADIUS),
        "aft_motor_tube",
    )
    aft_body_band = style_body_part(
        cylinder_between(AFT_BODY_SEAM_Z, AFT_BODY_SEAM_Z + 14.0, 95.5),
        "aft_body_joint_band",
        METAL_COLOR,
        0.45,
    )
    aft_body = style_body_part(
        cylinder_between(AFT_BODY_SEAM_Z + 14.0, FIRST_BODY_SEAM_Z, BODY_RADIUS),
        "aft_body",
    )
    center_band = style_body_part(
        cylinder_between(FIRST_BODY_SEAM_Z, FIRST_BODY_SEAM_Z + 18.0, 96.0),
        "center_joint_band",
        METAL_COLOR,
        0.45,
    )
    center_module = style_body_part(
        cylinder_between(FIRST_BODY_SEAM_Z + 18.0, SECOND_BODY_SEAM_Z, BODY_RADIUS),
        "center_module",
    )
    forward_band = style_body_part(
        cylinder_between(SECOND_BODY_SEAM_Z, SECOND_BODY_SEAM_Z + 18.0, 96.0),
        "forward_joint_band",
        METAL_COLOR,
        0.45,
    )
    forward_motor = style_body_part(
        cylinder_between(SECOND_BODY_SEAM_Z + 18.0, CONTROL_BAND_START_Z, BODY_RADIUS),
        "forward_motor_tube",
    )
    control_band = style_body_part(
        cylinder_between(CONTROL_BAND_START_Z, CONTROL_SECTION_START_Z, 96.0),
        "control_joint_band",
        METAL_COLOR,
        0.45,
    )
    control_section = style_body_part(
        cylinder_between(CONTROL_SECTION_START_Z, SEEKER_COLLAR_START_Z, BODY_RADIUS),
        "control_section",
    )
    seeker_collar = style_body_part(
        make_faceted_collar(), "seeker_mount_collar", METAL_COLOR, 0.45
    )
    nose_fairing = style_body_part(
        make_seeker_fairing(), "seeker_fairing"
    )
    seeker_bezel = style_body_part(
        cylinder_between(SEEKER_BEZEL_START_Z, GLASS_START_Z, 42.0),
        "seeker_window_bezel",
        METAL_COLOR,
        0.55,
    )
    ir_dome = style_body_part(
        make_ir_dome(), "ir_seeker_dome", SEEKER_COLOR
    )
    ir_dome.cad_material = {
        "roughness": 0.18,
        "metalness": 0.15,
        "clearcoat": 1.0,
        "clearcoatRoughness": 0.08,
    }

    vane_a = make_control_vane(
        VANE_A_START_Z, VANE_A_END_Z, VANE_A_TIP_RADIUS, edge_scale=1.5
    )
    vanes_a = [
        styled_part(vane_a, angle, f"rear_control_vane_{index}", FIN_COLOR)
        for index, angle in enumerate(GRID_FIN_AZIMUTHS)
    ]
    vane_b = make_forward_control_vane()
    vanes_b = [
        styled_part(vane_b, angle, f"forward_control_vane_{index}", FIN_COLOR)
        for index, angle in enumerate((45.0, 135.0, 225.0, 315.0))
    ]

    fairing = make_longitudinal_fairing()
    fairings = [
        styled_part(fairing, angle, f"aft_fairing_{index}", BODY_COLOR)
        for index, angle in enumerate(GRID_FIN_AZIMUTHS)
    ]

    grid_fin = make_grid_fin()
    grid_material = {"roughness": 0.5, "metalness": 0.65}
    grid_fins = [
        styled_part(grid_fin, angle, f"grid_fin_{index}", FIN_COLOR, grid_material)
        for index, angle in enumerate(GRID_FIN_AZIMUTHS)
    ]

    return bd.Compound(
        children=[
            nozzle,
            aft_collar,
            aft_motor,
            aft_body_band,
            aft_body,
            center_band,
            center_module,
            forward_band,
            forward_motor,
            control_band,
            control_section,
            seeker_collar,
            nose_fairing,
            seeker_bezel,
            ir_dome,
            *vanes_a,
            *vanes_b,
            *fairings,
            *grid_fins,
        ],
        label="IRM-S4_Kris",
    )


if __name__ == "__main__":
    kris()
