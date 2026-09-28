"""A8 rounded end study from user markup; A2 center remains unchanged."""

from cadgen import build123d as bd

from housing import cassettes, housing, solid_box
from sketched_ends import eased_sections, section


def forward_sensor():
    # Long and low forward curve; the small terminal face is only the place
    # for a provisional recessed sensor cue, not a squared-off nose block.
    stations = ((1325, 400, 0, -223, 20),
                (1410, 385, -5, -223, 24),
                (1490, 340, -25, -220, 27),
                (1580, 280, -50, -213, 33),
                (1660, 210, -69, -200, 36),
                (1710, 170, -78, -181, 35),
                (1750, 130, -90, -163, 28),
                (1775, 96, -101, -150, 22),
                (1790, 80, -108, -144, 16))
    shape = bd.Solid.make_loft([section(*s) for s in eased_sections(stations)],
                               ruled=True)
    shape -= solid_box("forward_sensor_recess", 8, 65, 24, (1791, 0, -126))
    shape.label = "forward_sensor_shell"
    return shape


def aft_sensor():
    stations = ((-1710, 85, -92, -132, 18),
                (-1695, 100, -84, -140, 20),
                (-1670, 150, -69, -155, 27),
                (-1630, 190, -54, -170, 32),
                (-1610, 230, -43, -178, 34),
                (-1530, 310, -19, -203, 32),
                (-1470, 365, -5, -215, 25),
                (-1400, 400, 0, -223, 18),
                (-1325, 400, 0, -223, 12))
    shape = bd.Solid.make_loft([section(*s) for s in eased_sections(stations)],
                               ruled=True)
    shape -= solid_box("aft_sensor_recess", 8, 65, 24, (-1711, 0, -112))
    shape.label = "aft_sensor_shell"
    return shape


def study(filled):
    frame = [part for part in housing() if part.label not in (
        "forward_sensor_shell", "aft_sensor_shell", "forward_aperture",
        "aft_aperture", "port_outer_rail", "starboard_outer_rail")]
    frame.extend((forward_sensor(), aft_sensor(),
                  solid_box("forward_aperture", 1, 60, 18, (1787.5, 0, -126)),
                  solid_box("aft_aperture", 1, 60, 18, (-1707.5, 0, -112))))
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
