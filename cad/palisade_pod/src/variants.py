"""Contrastive concept-only U-frame studies B (open crown) and C (slotted shell)."""

from cadgen import build123d as bd

from housing import cassettes, solid_box


def end_pair(style):
    ends = []
    for title, sign in (("forward", 1), ("aft", -1)):
        end = solid_box(f"{title}_sensor_shell", 165, 400, 223,
                        (sign * 1407.5, 0, -111.5))
        if style == "B":
            end = bd.chamfer(end.edges().filter_by(bd.Axis.X), length=55)
        else:
            end = bd.fillet(end.edges().filter_by(bd.Axis.X), radius=65)
        end -= solid_box("aperture_tool", 8, 108, 37,
                         (sign * 1491, 0, -109))
        end.label = f"{title}_sensor_shell"
        ends.extend((end, solid_box(f"{title}_aperture", 1, 102, 31,
                                    (sign * 1487.5, 0, -109))))
    return ends


def b_open_crown():
    """Faceted sensor wedges, split dorsal bridge and low chamfered rails."""
    pieces = [solid_box("central_crown", 2650, 218, 24, (0, 0, -12))]
    for sign, side in ((-1, "port"), (1, "starboard")):
        y = sign * 193
        rail = solid_box(f"{side}_chamfered_rail", 2650, 14, 199,
                         (0, y, -123.5))
        rail = bd.chamfer(rail.edges().filter_by(bd.Axis.X), length=5)
        rail.label = f"{side}_chamfered_rail"
        pieces.append(rail)
        pieces.append(solid_box(f"{side}_roof_shoulder", 2650, 56, 18,
                                (0, sign * 158, -9)))
    # Three roof ties and a central cap preserve the bridge architecture while
    # the two exposed 21-mm crown channels carry B's negative-space signature.
    for station in (-1180, 0, 1180):
        pieces.append(solid_box(f"roof_arch_{station}", 16, 400, 20,
                                (station, 0, -17)))
    return pieces + end_pair("B")


def c_slotted_shell():
    """Broad rounded sensor capsules and paired side-wall relief windows."""
    saddle = solid_box("broad_dorsal_saddle", 2650, 380, 30, (0, 0, -15))
    saddle -= solid_box("dorsal_valley_tool", 2500, 130, 12, (0, 0, -2))
    saddle.label = "broad_dorsal_saddle"
    pieces = [saddle]
    for sign, side in ((-1, "port"), (1, "starboard")):
        rail = solid_box(f"{side}_windowed_rail", 2650, 14, 199,
                         (0, sign * 193, -123.5))
        # Frame remains continuous above/below the side openings. The openings
        # expose only the cassette *skin*, not any fastener or launcher hardware.
        for x in (-660, 660):
            rail -= solid_box("window_tool", 760, 25, 34,
                              (x, sign * 193, -72))
        rail.label = f"{side}_windowed_rail"
        pieces.append(rail)
        pieces.append(solid_box(f"{side}_upper_chine", 2650, 14, 12,
                                (0, sign * 193, -18)))
    pieces.extend(end_pair("C"))
    return pieces


def study(style, filled):
    assert style in ("B", "C")
    housing = b_open_crown() if style == "B" else c_slotted_shell()
    return bd.Compound(children=housing + (cassettes() if filled else []))
