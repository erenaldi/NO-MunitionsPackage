"""A7: A2's level center beam and smoothly faired ends from the user sketch."""

from cadgen import build123d as bd

from housing import cassettes, housing, solid_box
from sketched_ends import aft_sensor, forward_sensor


def study(filled):
    frame = [part for part in housing() if part.label not in (
        "forward_sensor_shell", "aft_sensor_shell", "forward_aperture",
        "aft_aperture", "port_outer_rail", "starboard_outer_rail")]
    frame.extend((forward_sensor(level_root=True, eased=True), aft_sensor(eased=True),
                  solid_box("forward_aperture", 1, 105, 32, (1787.5, 0, -117)),
                  solid_box("aft_aperture", 1, 105, 32, (-1707.5, 0, -112))))
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
