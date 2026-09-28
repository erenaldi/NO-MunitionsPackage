"""HKP-1 concept A: straight bridge and twin perimeter-rail U frame, in mm.

These volumes are visual studies, not AGM2 launcher or moving shutter geometry.
X forward, Y starboard, Z up. The underside is negative Z.
"""

from cadgen import build123d as bd


LENGTH = 2980.0
WIDTH = 400.0
HEIGHT = 240.0
BOX_LENGTH = 1310.0
BOX_WIDTH = 180.0
BOX_HEIGHT = 180.0
BOX_X = (-664.0, 664.0)
BOX_Y = (-95.0, 95.0)
BOX_Z = -133.0  # underside -223, top -43; no bottom frame below cells


def solid_box(label, length, width, height, center):
    shape = bd.Box(length, width, height).translate(center)
    shape.label = label
    return shape


def housing():
    """Bare housing: load-bearing perimeter, cross-bridge and sensor ends."""
    forward = solid_box("forward_sensor_shell", 165, 400, 223, (1407.5, 0, -111.5))
    aft = solid_box("aft_sensor_shell", 165, 400, 223, (-1407.5, 0, -111.5))
    forward -= solid_box("forward_recess_tool", 8, 110, 36, (1491, 0, -113))
    aft -= solid_box("aft_recess_tool", 8, 110, 36, (-1491, 0, -113))
    forward.label = "forward_sensor_shell"
    aft.label = "aft_sensor_shell"
    pieces = [
        solid_box("dorsal_bridge", 2650, 380, 30, (0, 0, -15)),
        solid_box("port_outer_rail", 2650, 14, 199, (0, -193, -123.5)),
        solid_box("starboard_outer_rail", 2650, 14, 199, (0, 193, -123.5)),
        # Small ledges stop above the cassette underside; the mounts disappear
        # behind the filled skins. No full-width beam obstructs downward exits.
        solid_box("port_landing", 2600, 11, 10, (0, -180.5, -33)),
        solid_box("starboard_landing", 2600, 11, 10, (0, 180.5, -33)),
        solid_box("central_spine", 2620, 8, 25, (0, 0, -36.5)),
        solid_box("middle_top_tie", 18, 370, 16, (0, 0, -32)),
        forward,
        aft,
        solid_box("forward_aperture", 1, 105, 32, (1487.5, 0, -113)),
        solid_box("aft_aperture", 1, 105, 32, (-1487.5, 0, -113)),
    ]
    return pieces


def cassettes(side_skin=False):
    """A2 boxes span to the 400 mm outer skin; earlier studies stay frozen."""
    width = 196.0 if side_skin else BOX_WIDTH
    ys = (-102.0, 102.0) if side_skin else BOX_Y
    return [solid_box(f"cassette_{row}_{side}", BOX_LENGTH, width, BOX_HEIGHT,
                      (x, y, BOX_Z)) for row, x in zip(("aft", "forward"), BOX_X)
            for side, y in zip(("port", "starboard"), ys)]


def make_study(filled):
    return bd.Compound(children=housing() + (cassettes() if filled else []))


def make_open_side_study(filled):
    """Selected-A revision: no full-height side skin hiding the four boxes."""
    frame = [part for part in housing() if not part.label.endswith("_outer_rail")]
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame + (cassettes(side_skin=True) if filled else []))
