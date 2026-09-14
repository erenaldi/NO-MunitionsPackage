from cadgen import build123d as bd
from cadgen import step


LENGTH = 3400.0
BODY_RADIUS = 115.0
DOME_BASE_Z = 3310.0
SEEKER_RADIUS = LENGTH - DOME_BASE_Z
NECK_RADIUS = SEEKER_RADIUS
CENTER_JOINT_RADIUS = 117.0
FORWARD_CONNECTOR_RADIUS = 120.0
MOTOR_HOUSING_AFT_RADIUS = 108.0
MOTOR_HOUSING_BORE_RADIUS = 84.0
NOZZLE_END_Z = 65.0
AFT_RING_START_Z = 35.0
MOTOR_HOUSING_START_Z = 55.0
MOTOR_FLARE_END_Z = 80.0
MOTOR_BORE_TAPER_END_Z = 120.0
MOTOR_BORE_END_Z = 160.0
MOTOR_TUBE_START_Z = 350.0
CENTER_JOINT_START_Z = 1500.0
CENTER_JOINT_END_Z = 1530.0
FORWARD_CONNECTOR_START_Z = 2440.0
SHOULDER_START_Z = 2500.0
NECK_START_Z = 2600.0
BAND_START_Z = 2860.0
SEEKER_START_Z = 2960.0


def circle_section(z, radius, x_offset=0.0):
    return bd.Circle(radius).translate((x_offset, 0.0, z), transform=True)


def cylinder_between(z_min, z_max, radius):
    cylinder = bd.Cylinder(
        radius,
        z_max - z_min,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    )
    return cylinder.translate((0.0, 0.0, z_min), transform=True)


def annular_loft(outer_sections, inner_sections):
    outer = bd.loft(
        [circle_section(z, radius) for z, radius in outer_sections],
        ruled=True,
    )
    inner = bd.loft(
        [circle_section(z, radius) for z, radius in inner_sections],
        ruled=True,
    )
    return outer - inner


def make_ir_dome():
    dome = bd.Sphere(
        SEEKER_RADIUS,
        arc_size1=0.0,
        arc_size2=90.0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    )
    return dome.translate((0.0, 0.0, DOME_BASE_Z), transform=True)


def make_forward_sections():
    seeker_body = cylinder_between(SEEKER_START_Z, DOME_BASE_Z, SEEKER_RADIUS)
    identification_band = cylinder_between(
        BAND_START_Z, SEEKER_START_Z, SEEKER_RADIUS
    )
    neck = cylinder_between(NECK_START_Z, BAND_START_Z, NECK_RADIUS)
    shoulder = bd.loft(
        [
            circle_section(SHOULDER_START_Z, BODY_RADIUS),
            circle_section(NECK_START_Z, NECK_RADIUS),
        ],
        ruled=True,
    )
    return shoulder, neck, identification_band, seeker_body


def make_main_body():
    aft_tube = cylinder_between(MOTOR_TUBE_START_Z, CENTER_JOINT_START_Z, BODY_RADIUS)
    center_joint = cylinder_between(
        CENTER_JOINT_START_Z, CENTER_JOINT_END_Z, CENTER_JOINT_RADIUS
    )
    forward_tube = cylinder_between(
        CENTER_JOINT_END_Z, FORWARD_CONNECTOR_START_Z, BODY_RADIUS
    )
    forward_connector = cylinder_between(
        FORWARD_CONNECTOR_START_Z, SHOULDER_START_Z, FORWARD_CONNECTOR_RADIUS
    )
    return aft_tube, center_joint, forward_tube, forward_connector


def make_motor_assembly():
    motor_housing = annular_loft(
        [
            (MOTOR_HOUSING_START_Z, MOTOR_HOUSING_AFT_RADIUS),
            (MOTOR_FLARE_END_Z, BODY_RADIUS),
            (MOTOR_TUBE_START_Z, BODY_RADIUS),
        ],
        [
            (MOTOR_HOUSING_START_Z, MOTOR_HOUSING_BORE_RADIUS),
            (MOTOR_BORE_TAPER_END_Z, 70.0),
            (MOTOR_BORE_END_Z, 70.0),
        ],
    )
    aft_end_ring = annular_loft(
        [
            (AFT_RING_START_Z, MOTOR_HOUSING_AFT_RADIUS),
            (MOTOR_HOUSING_START_Z, MOTOR_HOUSING_AFT_RADIUS),
        ],
        [
            (AFT_RING_START_Z, MOTOR_HOUSING_BORE_RADIUS),
            (MOTOR_HOUSING_START_Z, MOTOR_HOUSING_BORE_RADIUS),
        ],
    )
    exhaust_nozzle = annular_loft(
        [(0.0, 80.0), (NOZZLE_END_Z, 60.0)],
        [(0.0, 58.0), (NOZZLE_END_Z, 30.0)],
    )
    return motor_housing, aft_end_ring, exhaust_nozzle


@step(out="AAM41_Basilisk.step")
def basilisk():
    ir_dome = make_ir_dome()
    ir_dome.label = "ir_seeker_dome"

    shoulder, neck, identification_band, seeker_body = make_forward_sections()
    shoulder.label = "forward_shoulder"
    neck.label = "seeker_neck"
    identification_band.label = "identification_band"
    seeker_body.label = "seeker_body"

    aft_tube, center_joint, forward_tube, forward_connector = make_main_body()
    aft_tube.label = "aft_motor_tube"
    center_joint.label = "center_joint"
    forward_tube.label = "forward_motor_tube"
    forward_connector.label = "forward_connector"

    motor_housing, aft_end_ring, exhaust_nozzle = make_motor_assembly()
    motor_housing.label = "motor_housing"
    aft_end_ring.label = "aft_end_ring"
    exhaust_nozzle.label = "exhaust_nozzle"

    assembly = bd.Compound(
        children=[
            exhaust_nozzle,
            aft_end_ring,
            motor_housing,
            aft_tube,
            center_joint,
            forward_tube,
            forward_connector,
            shoulder,
            neck,
            identification_band,
            seeker_body,
            ir_dome,
        ],
        label="AAM41_Basilisk",
    )
    return assembly


if __name__ == "__main__":
    basilisk()
