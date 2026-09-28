"""A5 — covered recess with full-law joint-pin sweep clearance.

The eleven A4 nonbody parts are reused with one additional rigid Z shift.
The body starts from the original A2 factory and receives only the approved
well, shifted side slots, cover seat, and analytic pin-sweep cutters.
"""
import math

from cadgen import build123d as bd, srgb, step
from interleaved_wing_a import pose as a_pose
from interleaved_wing_a2 import body as a2_body, box
from interleaved_wing_a4 import BODY_LABEL, components as a4_components
from joined_wing_r1 import (
    FRONT_LENGTH,
    OPEN_SEPARATION,
    REAR_LENGTH,
    STOW_SEPARATION,
)

DROP = 5.5
CLEARANCE = 0.3
SHAFT_RADIUS = 3.5
CAP_RADIUS = 7.0
WELL = (-450.3, 550.3, -74.3, 74.3, 57.75, 84.0)
SLOTS_A4 = (
    (-430.0, 530.0, 0.0, 100.0, 65.7, 70.3),
    (-430.0, 530.0, 0.0, 100.0, 76.2, 80.8),
    (-430.0, 530.0, -100.0, 0.0, 71.2, 75.8),
    (-430.0, 530.0, -100.0, 0.0, 81.7, 86.3),
)
COVER = (-455.0, 555.0, -76.0, 76.0, 84.0, 86.0)
COVER_SEAT = (-455.0, 555.0, -76.0, 76.0, 84.0, 100.0)

# Trial ranges are the measured A4 saved-join shaft/cap intervals from
# reviews/covered_a5_probe.json, shifted down 5.5 mm. Starboard and port are
# intentionally distinct. Their radial/Z tool clearances are applied below.
TRIAL_JOIN_Z = {
    "starboard": {"shaft": (60.25, 75.25), "cap": (75.25, 75.75)},
    "port": {"shaft": (65.75, 80.75), "cap": (80.75, 81.25)},
}


def cylinder(radius, z0, z1, xy):
    """A Z-aligned cutter cylinder with its bottom at z0."""
    return bd.Cylinder(
        radius,
        z1 - z0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    ).translate((xy[0], xy[1], z0))


def annular_sector(cx, cy, radius, z0, z1, theta0, theta1):
    """Revolve a radial/Z rectangle through the requested full angle interval."""
    inner, outer = FRONT_LENGTH - radius, FRONT_LENGTH + radius
    theta = math.radians(theta0)
    points = [
        (cx + inner * math.cos(theta), cy + inner * math.sin(theta), z0),
        (cx + outer * math.cos(theta), cy + outer * math.sin(theta), z0),
        (cx + outer * math.cos(theta), cy + outer * math.sin(theta), z1),
        (cx + inner * math.cos(theta), cy + inner * math.sin(theta), z1),
    ]
    profile = bd.Face(bd.Wire.make_polygon(points, close=True))
    return bd.revolve(
        profile,
        axis=bd.Axis((cx, cy, 0), (0, 0, 1)),
        revolution_arc=theta1 - theta0,
    ).clean()


def joint_sweep_extrema(side):
    """Return analytic angular extrema and their exact joint-center positions.

    The link-law axial leg has its stationary point at separation
    sqrt(FRONT_LENGTH**2 - REAR_LENGTH**2), which is interior to the motion.
    Including that pose captures the angle reversal before fraction 1.
    """
    critical_separation = math.sqrt(FRONT_LENGTH**2 - REAR_LENGTH**2)
    critical_fraction = (
        (critical_separation - STOW_SEPARATION)
        / (OPEN_SEPARATION - STOW_SEPARATION)
    )
    center = a_pose(0.0, side)["front"]
    candidates = []
    for fraction in (0.0, critical_fraction, 1.0):
        joint = a_pose(fraction, side)["joint"]
        theta = math.degrees(
            math.atan2(joint[1] - center[1], joint[0] - center[0])
        )
        candidates.append((theta, (float(joint[0]), float(joint[1]))))
    low = min(candidates, key=lambda candidate: candidate[0])
    high = max(candidates, key=lambda candidate: candidate[0])
    return low[0], high[0], (low[1], high[1])


def pin_sweep_cutters(body_source=None):
    """Return the four pin-sweep cutters clipped to the original A2 body."""
    if body_source is None:
        body_source = a2_body()

    tools = []
    for side in ("starboard", "port"):
        center = a_pose(0.0, side)["front"]
        theta_lo, theta_hi, extrema_centers = joint_sweep_extrema(side)
        for feature, nominal_radius in (
            ("shaft", SHAFT_RADIUS),
            ("cap", CAP_RADIUS),
        ):
            z_trial = TRIAL_JOIN_Z[side][feature]
            z0 = z_trial[0] - CLEARANCE
            z1 = z_trial[1] + CLEARANCE
            tool_radius = nominal_radius + CLEARANCE
            sector = annular_sector(
                center[0], center[1], tool_radius, z0, z1, theta_lo, theta_hi
            )
            endpoint_discs = [
                cylinder(tool_radius, z0, z1, point)
                for point in extrema_centers
            ]
            raw_tool = (sector + endpoint_discs[0] + endpoint_discs[1]).clean()
            tools.append((raw_tool & body_source).clean())
    return tools


def fixed_cutters():
    """Return the exact well, A4 slots shifted -5.5 mm, and cover-seat cut."""
    cutters = [box(*WELL)]
    cutters.extend(
        box(x0, x1, y0, y1, z0 - DROP, z1 - DROP)
        for x0, x1, y0, y1, z0, z1 in SLOTS_A4
    )
    cutters.append(box(*COVER_SEAT))
    return cutters


def body_cutters(body_source=None):
    """Expose the full cutter set used to form the A5 recessed body."""
    return fixed_cutters() + pin_sweep_cutters(body_source)


def body_recessed():
    """Cut the A5 recess from the original A2 body and preserve its label."""
    original = a2_body()
    cutters = body_cutters(original)
    tool_union = cutters[0]
    for cutter in cutters[1:]:
        tool_union = tool_union + cutter
    recessed = (original - tool_union).clean()
    recessed.label = BODY_LABEL
    return recessed


def top_cover():
    """Return the specified neutral-body-color 2 mm cover plate."""
    cover = box(*COVER)
    cover.label = "top_cover"
    cover.color = srgb("#A7B4BC")
    return cover


def components(fraction):
    """Return all eleven A4 components under the additional rigid Z drop."""
    return [part.translate((0, 0, -DROP)) for part in a4_components(fraction)]


def assembly(fraction, full=True):
    parts = components(fraction)
    parts.append(top_cover())
    if full:
        parts.insert(0, body_recessed())
    return bd.Compound(children=parts, label="Phantom_interleaved_A5")


@step(out="../STEP/O_Interleaved_A5_Stowed.step")
def stowed():
    return assembly(0.0)


@step(out="../STEP/O_Interleaved_A5_Module_Stowed.step")
def module_stowed():
    return assembly(0.0, False)


@step(out="../STEP/O_Interleaved_A5_Midfold.step")
def midfold():
    return assembly(0.5)


@step(out="../STEP/O_Interleaved_A5_Deployed.step")
def deployed():
    return assembly(1.0)


@step(out="../STEP/O_Interleaved_A5_Body_Pocket.step")
def body_pocket():
    return body_recessed()


@step(out="../STEP/O_Interleaved_A5_Cover.step")
def cover_only():
    return top_cover()


if __name__ == "__main__":
    stowed()
    module_stowed()
    midfold()
    deployed()
    body_pocket()
    cover_only()
