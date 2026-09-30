"""R19 even inlet side walls (2026-09-29 user direction).

The inherited inlet (intake_r3/r4/r6 shapes) cuts a channel whose side face is
not parallel to the housing's outer side face, so each side wall seen at the
swept mouth tapers from ~3.6 mm at the roof to ~1.1 mm at the floor, while the
roof wall is ~3.5 mm. The user asked for side walls of constant thickness,
slightly thinner than the roof wall.

This re-cuts only the front of the channel on the saved R12-lineage host:
the old channel segment (X 350 to the mouth) is filled solid, then the new
channel (side face offset SIDE_WALL inward from the outer side face, roof and
floor unchanged) is cut into it. Filling first matters: cutting only the new
band leaves the tool's roof/floor faces coincident with the old channel's,
and OCC then skips the cut silently. The cutter starts 10 mm aft of the fill
inside the old channel (same section there) so no end faces coincide. The historical intake sources are not
edited, so earlier revisions rebuild unchanged. Cosmetic geometry only.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd

from intake_r3_shapes import (CORE_RADIUS, CORNER_CENTER, CORNER_RADIUS, ENTRY_SWEEP,
                              MOUTH_FOOT_X, WALL, core_height, inner_profile)
from intake_r5_shapes import FRONT_END, TAPER_START
from study_shapes import rotate

SIDE_WALL = 3.0                     # roof wall at the mouth is ~3.2-3.6 mm
CLOCKS = (45.0, 135.0, 225.0, 315.0)
OUTER_HALF, OUTER_ROOF_HALF = 44.0, 16.0
INNER_ROOF = 142.0                  # passage roof, X 560-735 (unchanged)
FLOOR_RADIUS = CORE_RADIUS + WALL   # concentric floor (unchanged)
# Inherited channel stations (intake_r3 passage / intake_r4 extended_passage).
OLD_STATIONS = ((350.0, 36.0, 13.0, 143.5), (560.0, 38.0, 13.5, 142.0),
                (735.0, 38.0, 13.5, 142.0))


def precise_volume(shape):
    """Volume with tight Gauss integration. Default-precision volumes of the
    thin inlet gain solids err by ~2e-4 relative (2026-09-29: 10278.23 vs
    10276.68 mm3 for identical solids); at eps 1e-9 they agree exactly."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    total = 0.0
    for solid in shape.solids():
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(solid.wrapped, props, 1e-9, True, True)
        total += props.Mass()
    return total


def outer_roof(x):
    """Outer housing roof height of the ruled front loft (147.5 -> 145)."""
    return 147.5 + (145.0 - 147.5) * (x - TAPER_START) / (FRONT_END - TAPER_START)


def _offset_side(x):
    """Inward-offset outer side line at X: (point, direction) in local (y, z)."""
    foot = (OUTER_HALF, core_height(OUTER_HALF) - 0.4)
    top = (OUTER_ROOF_HALF, outer_roof(x))
    dy, dz = top[0] - foot[0], top[1] - foot[1]
    length = math.hypot(dy, dz)
    dy, dz = dy / length, dz / length
    ny, nz = -dz, dy                 # inward normal (towards the channel)
    if ny > 0.0:
        ny, nz = -ny, -nz
    return (foot[0] + SIDE_WALL * ny, foot[1] + SIDE_WALL * nz), (dy, dz)


def even_station(x):
    """(x, floor_half, roof_half, roof) for a channel with SIDE_WALL side walls."""
    (py, pz), (dy, dz) = _offset_side(x)
    roof_half = py + (INNER_ROOF - pz) / dz * dy

    def floor_gap(y):   # offset-line z minus floor-arc z at tangent y
        return pz + (y - py) / dy * dz - (CORNER_CENTER + math.sqrt(FLOOR_RADIUS ** 2 - y * y))

    lo, hi = 20.0, 60.0
    if floor_gap(lo) * floor_gap(hi) > 0.0:
        raise ValueError(("offset side line misses the channel floor", x))
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if floor_gap(lo) * floor_gap(mid) <= 0.0:
            hi = mid
        else:
            lo = mid
    return (x, (lo + hi) / 2.0, roof_half, INNER_ROOF)


NEW_STATIONS = (OLD_STATIONS[0], even_station(560.0), even_station(735.0))
# Inherited channel section at X=340 (linear between the 210 and 350 stations).
LEAD_IN = (340.0, 35.0 + 130.0 / 140.0, 12.0 + 130.0 / 140.0, 143.8 - 0.3 * 130.0 / 140.0)


def _channel(stations):
    return bd.loft([inner_profile(*s) for s in stations], ruled=True)


def _mouth_cut():
    """The inherited swept-mouth cutter (intake_r6 curved_outer), local frame."""
    def front_x(radial):
        return MOUTH_FOOT_X - ENTRY_SWEEP * (radial - CORNER_RADIUS)
    face = bd.Face(bd.Wire.make_polygon([
        (front_x(75.0), -120.0, 75.0), (850.0, -120.0, 75.0),
        (850.0, -120.0, 200.0), (front_x(200.0), -120.0, 200.0)], close=True))
    return bd.extrude(face, amount=240.0, dir=(0, 1, 0))


def wall_tools(clock):
    """(fill, cut) solids in world frame for the inlet at ``clock``."""
    fill = _channel(OLD_STATIONS) - _mouth_cut()
    cut = _channel((LEAD_IN, *NEW_STATIONS))
    return rotate(fill, clock), rotate(cut, clock)


def even_intake_walls(host):
    """Return (host, info): all four inlets re-cut with even side walls."""
    info = {"side_wall_mm": SIDE_WALL, "stations": {"old": OLD_STATIONS, "new": NEW_STATIONS},
            "inlets": {}}
    for clock in CLOCKS:
        fill, cut = wall_tools(clock)
        before = host.volume
        host = host + fill
        added = host.volume - before
        if abs(added - fill.volume) > 1e-3 * fill.volume:
            raise ValueError(("inlet wall fill added no material", clock, added, fill.volume))
        mid = host.volume
        host = host - cut
        removed = mid - host.volume
        if removed <= 1e-3:
            raise ValueError(("inlet channel re-cut removed no material", clock))
        if not host.is_valid or len(host.solids()) != 1:
            raise ValueError(("inlet re-cut invalidated the host", clock))
        info["inlets"][f"{clock:g}"] = {"fill_mm3": added, "cut_mm3": removed}
    return host, info
