"""A6 side-sketch interpretation: smooth rounded sensor prow at both ends.

This is a reversible silhouette study; the user drawing is shape intent, not
an orthographic dimensioned drawing. Central A2 box/side architecture is fixed.
"""

from cadgen import build123d as bd

from housing import cassettes, housing, solid_box
from mount_front import rounded_section
from mount_front_long import dorsal_bridge


def eased_sections(stations, subdivisions=4):
    """PCHIP-style bounded tangents keep the contour smooth without overshoot."""
    xs = [row[0] for row in stations]

    def slopes(values):
        h = [b-a for a, b in zip(xs, xs[1:])]
        delta = [(b-a)/step for a, b, step in zip(values, values[1:], h)]
        if len(delta) == 1:
            return [delta[0], delta[0]]
        derivatives = []

        def endpoint(first, second, near, far):
            slope = ((2*near+far)*first-near*second)/(near+far)
            if slope*first <= 0:
                return 0.
            if first*second <= 0 and abs(slope) > abs(3*first):
                return 3*first
            return slope

        derivatives.append(endpoint(delta[0], delta[1], h[0], h[1]))
        for i in range(1, len(values)-1):
            prev, next_ = delta[i-1], delta[i]
            if prev*next_ <= 0:
                derivatives.append(0.)
            else:
                w1, w2 = 2*h[i]+h[i-1], h[i]+2*h[i-1]
                derivatives.append((w1+w2)/(w1/prev+w2/next_))
        derivatives.append(endpoint(delta[-1], delta[-2], h[-1], h[-2]))
        return derivatives

    columns = [tuple(row[j] for row in stations) for j in range(1, len(stations[0]))]
    tangents = [slopes(values) for values in columns]
    result = []
    for idx, (start, end) in enumerate(zip(stations, stations[1:])):
        step = end[0]-start[0]
        for i in range(subdivisions):
            t = i/subdivisions
            h00, h10 = 2*t**3-3*t**2+1, t**3-2*t**2+t
            h01, h11 = -2*t**3+3*t**2, t**3-t**2
            values = []
            for column, tangent in zip(columns, tangents):
                value = (h00*column[idx]+h10*step*tangent[idx]+h01*column[idx+1]
                         +h11*step*tangent[idx+1])
                values.append(value)
            result.append((start[0]+step*t, *values))
    result.append(stations[-1])
    return result


def section(x, width, top, bottom, corner):
    return rounded_section(x, width, top-bottom, corner, (top+bottom)/2)


def forward_sensor(ruled=True, level_root=False, eased=False):
    # Nose length is 465 mm measured from the existing front-beam boundary.
    # Its lower contour stays nearly level early, then rises to a blunt tip.
    root_tops = (0, -5, -25) if level_root else (-13, -20, -34)
    stations = ((1325, 400, root_tops[0], -223, 20),
                (1410, 385, root_tops[1], -223, 24),
                (1490, 340, root_tops[2], -220, 27),
                (1580, 280, -50, -213, 33),
                (1660, 210, -69, -200, 36),
                (1740, 150, -83, -164, 30),
                (1790, 140, -91, -144, 20))
    shape = bd.Solid.make_loft(
        [section(*s) for s in (eased_sections(stations) if eased else stations)],
        ruled=ruled)
    shape -= solid_box("forward_recess_tool", 8, 110, 36, (1791, 0, -117))
    shape.label = "forward_sensor_shell"
    return shape


def aft_sensor(ruled=True, eased=False):
    # Shorter aft end in the annotated side view: shallow rounded tip, broad
    # shoulders meeting the existing frame at X=-1325. No center side cover.
    stations = ((-1710, 160, -77, -147, 25),
                (-1680, 170, -69.5, -154.5, 28),
                (-1610, 230, -43, -178, 34),
                (-1530, 310, -19, -203, 32),
                (-1470, 365, -5, -215, 25),
                (-1400, 400, 0, -223, 18),
                (-1325, 400, 0, -223, 12))
    shape = bd.Solid.make_loft(
        [section(*s) for s in (eased_sections(stations) if eased else stations)],
        ruled=ruled)
    shape -= solid_box("aft_recess_tool", 8, 110, 36, (-1711, 0, -112))
    shape.label = "aft_sensor_shell"
    return shape


def study(filled):
    frame = [part for part in housing() if part.label not in (
        "dorsal_bridge", "forward_sensor_shell", "aft_sensor_shell",
        "forward_aperture", "aft_aperture", "port_outer_rail",
        "starboard_outer_rail")]
    frame.extend((dorsal_bridge(), forward_sensor(), aft_sensor(),
                  solid_box("forward_aperture", 1, 105, 32, (1787.5, 0, -117)),
                  solid_box("aft_aperture", 1, 105, 32, (-1707.5, 0, -112))))
    for sign, side in ((-1, "port"), (1, "starboard")):
        frame.append(solid_box(f"{side}_outer_rail", 2650, 14, 19,
                               (0, sign*193, -33.5)))
    return bd.Compound(children=frame+(cassettes(side_skin=True) if filled else []))
