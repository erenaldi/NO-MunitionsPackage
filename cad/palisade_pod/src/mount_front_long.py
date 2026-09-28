"""A4 extended mount-like dorsal taper with a lower-height forward sensor end."""

from cadgen import build123d as bd

from housing import cassettes, housing, solid_box
from mount_front import rounded_section


def roof_profile(x, top):
    return bd.Wire.make_polygon(((x, -190, -30), (x, 190, -30),
                                 (x, 190, top), (x, -190, top)), close=True)


def dorsal_bridge():
    back = solid_box("rear_bridge", 1975, 380, 30, (-337.5, 0, -15))
    fore = bd.Solid.make_loft([roof_profile(x, top) for x, top in
                               ((649.9, 0), (950, -2), (1150, -6),
                                (1325, -13))], ruled=True)
    bridge = back + fore
    bridge.label = "dorsal_bridge"
    return bridge


def forward_sensor():
    # Each section's upper surface descends toward +X while overall height
    # contracts. It remains inside the original A2 block and clears four cells.
    stations = ((1325, 400, 210, 20, -118),
                (1360, 400, 203, 25, -118.5),
                (1420, 370, 178, 34, -118),
                (1460, 310, 149, 42, -116.5),
                (1490, 270, 125, 50, -117.5))
    fairing = bd.Solid.make_loft(
        [rounded_section(*section) for section in stations], ruled=True)
    fairing -= solid_box("forward_recess_tool", 8, 110, 36, (1491, 0, -113))
    fairing.label = "forward_sensor_shell"
    return fairing


def study(filled):
    frame = [part for part in housing() if part.label not in
             ("dorsal_bridge", "forward_sensor_shell", "port_outer_rail",
              "starboard_outer_rail")]
    frame.extend((dorsal_bridge(), forward_sensor()))
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
