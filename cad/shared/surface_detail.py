"""Asset-agnostic helpers for conformal surface detailing on X-axis bodies.

Extracted from the Halberd R19 prototype (2026-09-28). Lessons behind them are
in ~/.claude/domain/cad.md ("Surface detailing construction"):

- Find skin points with one native ray/face intersection. The R18 stepped
  inside/outside search plus all-face scan cost 3-10 s per point; this costs
  about 0.02 s and matched it to 1e-7 mm on the Halberd forward section.
- Every Boolean cut must prove it removed material: OCC can silently return
  the host unchanged (seen on the Halberd nose-joint ring seats).
- Do not batch cutters into one multi-tool OCC cut without a volume check; on
  the Halberd prototype it over-removed material and was not faster.

Conventions: body axis +X; ``clock`` in degrees with 0 = +Z and 90 = +Y
(radial = (0, sin, cos)); ``tangent_offset`` is along (0, cos, -sin).

Import from an asset folder with:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
"""
from __future__ import annotations

import math

from cadgen import build123d as bd


def clock_frame(clock_degrees):
    """Return (radial, tangent) unit vectors for a clock angle about +X."""
    angle = math.radians(clock_degrees)
    radial = bd.Vector(0.0, math.sin(angle), math.cos(angle))
    tangent = bd.Vector(0.0, math.cos(angle), -math.sin(angle))
    return radial, tangent


def _ray_hits(shape, origin, direction, tolerance=1e-6):
    """Native ray/face hits as (distance, point, face), nearest first."""
    from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
    from OCP.gce import gce_MakeLin

    line = gce_MakeLin(bd.Axis(origin, direction).wrapped).Value()
    hits = BRepIntCurveSurface_Inter()
    hits.Init(shape.wrapped, line, tolerance)
    found = []
    while hits.More():
        if hits.W() >= 0.0:
            found.append((hits.W(), bd.Vector(hits.Pnt()), bd.Face(hits.Face())))
        hits.Next()
    return sorted(found, key=lambda row: row[0])


def skin_point(host, x, tangent_offset, clock, max_radius=260.0):
    """Outer skin point, face and outward normal from one inward ray.

    Raises when the ray misses, lands on a face that does not face outward,
    or the hit point has no material just beneath it.
    """
    radial, tangent = clock_frame(clock)
    base = bd.Vector(x, 0.0, 0.0) + tangent * tangent_offset
    hits = _ray_hits(host, base + radial * max_radius, -radial)
    if not hits:
        raise ValueError(("skin ray missed the host", x, tangent_offset, clock))
    _, point, face = hits[0]
    normal = face.normal_at(point).normalized()
    if normal.dot(radial) < 0.0:
        normal = -normal
    if normal.dot(radial) < 0.25:
        raise ValueError(("skin ray hit a non-outward face", x, tangent_offset, clock))
    if not host.is_inside(point - normal * 0.05):
        raise ValueError(("skin ray point lacks host backing", x, tangent_offset, clock))
    return {"point": point, "normal": normal, "face": face,
            "measured_radius_mm": (point - base).dot(radial)}


def backing_depth(host, point, outward, max_depth=400.0):
    """Material depth beneath a skin point along -outward (first exit crossing)."""
    outward = bd.Vector(outward).normalized()
    start = bd.Vector(point) + outward * 0.01
    for distance, _hit, _face in _ray_hits(host, start, -outward):
        depth = distance - 0.01
        if 0.01 < depth <= max_depth and not host.is_inside(start - outward * (distance + 0.01)):
            return depth
    raise ValueError(("no backing exit found within bound", tuple(point), max_depth))


def checked_cut(host, cutter, minimum=1e-3):
    """``host - cutter`` that fails loudly if no material was removed."""
    result = host - cutter
    if not result or result.volume > host.volume - minimum:
        raise ValueError(("cutter removed no host material", getattr(cutter, "label", "")))
    return result


def seated_hardware(host, center_x, clock, offsets, seat_tool, head_tool, *,
                    seat_depth, min_remaining_wall, label_prefix, color=None):
    """Place local fastener seat/head tools on ray-measured skin sites.

    ``seat_tool``/``head_tool`` are built in a local frame with +Z outward and
    +X along the body axis, origin on the skin surface. Returns
    (seats, heads, sites); cut the seats from the host, add the heads as parts.
    """
    seats, heads, sites = [], [], []
    for index, (offset_x, offset_tangent) in enumerate(offsets, 1):
        surface = skin_point(host, center_x + offset_x, offset_tangent, clock)
        point, normal = surface["point"], surface["normal"]
        wall = backing_depth(host, point, normal)
        remaining = wall - seat_depth
        if remaining <= min_remaining_wall:
            raise ValueError((label_prefix, index, wall, "fastener has insufficient backing"))
        axis = bd.Vector(1.0, 0.0, 0.0)
        x_direction = axis - normal * normal.dot(axis)
        plane = bd.Plane(origin=point, x_dir=x_direction, z_dir=normal)
        seat = seat_tool.moved(plane.location)
        head = head_tool.moved(plane.location)
        seat.label = f"{label_prefix}_seat_{index}"
        head.label = f"{label_prefix}_fastener_{index}"
        if color is not None:
            head.color = color
        seats.append(seat)
        heads.append(head)
        sites.append({
            "offset_x_mm": float(offset_x),
            "offset_tangent_mm": float(offset_tangent),
            "point_mm": [point.X, point.Y, point.Z],
            "outward_normal": [normal.X, normal.Y, normal.Z],
            "measured_skin_radius_mm": surface["measured_radius_mm"],
            "available_wall_mm": wall,
            "remaining_wall_after_seat_mm": remaining,
        })
    return tuple(seats), tuple(heads), tuple(sites)
