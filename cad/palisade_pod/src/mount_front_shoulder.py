"""A5 mount-front cover: visible raised shoulder flowing into the low front."""

from cadgen import build123d as bd

from housing import cassettes, housing, solid_box
from mount_front import rounded_section
from mount_front_long import dorsal_bridge as a4_bridge, forward_sensor


def dorsal_bridge():
    bridge = a4_bridge()
    # The mount-photo cue is a shaped cover that begins *on* the dorsal beam
    # and has a visible shoulder. It is fused into the same roof solid, not a
    # side panel or a projectile. The 3-6 mm bottom overlap is intentional.
    sections = ((740, 320, 5, 1.5, -2.5),
                (810, 330, 34, 4, 11),
                (1000, 335, 34, 6, 9),
                (1150, 330, 28, 6, 4),
                (1260, 320, 20, 5, -4),
                (1325, 310, 9, 2.5, -14.5))
    cover = bd.Solid.make_loft(
        [rounded_section(*section) for section in sections], ruled=True)
    bridge += cover
    bridge.label = "dorsal_bridge"
    return bridge


def study(filled):
    frame = [part for part in housing() if part.label not in
             ("dorsal_bridge", "forward_sensor_shell", "port_outer_rail",
              "starboard_outer_rail")]
    frame.extend((dorsal_bridge(), forward_sensor()))
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
