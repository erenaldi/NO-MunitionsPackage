"""Fin-root / junction geometry helpers (extracted from the R20 seats and R21 bands).

Clock convention: 0 = +Z, 90 = +Y, rotation about +X; `clock_frame` in
`surface_detail` returns (radial, tangent). Nothing here runs at import time.

`RootSide` measures the skin beside one side of a fin root at any station (root edge,
land, crease) with bisection on native ray/face hits, so seats and bands can follow the
real surface instead of guessing. Pass `crop` (the host cut to a small box around the
work) so every ray is local and cheap.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd

from surface_detail import clock_frame, skin_point


def bisect(pred, lo, hi, iterations=22):
    """pred(lo) False, pred(hi) True -> boundary."""
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        if pred(mid):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def chamfered(points, size):
    """Cut each corner of a closed polygon by `size` (two points per corner)."""
    out = []
    n = len(points)
    for i, p in enumerate(points):
        for q in (points[i - 1], points[(i + 1) % n]):   # towards previous, then next
            d = math.hypot(q[0] - p[0], q[1] - p[1])
            out.append((p[0] + (q[0] - p[0]) * size / d, p[1] + (q[1] - p[1]) * size / d))
    return out


def densify(points, spacing=1.0):
    """Subdivide a closed polygon so no edge is longer than `spacing`."""
    dense = []
    n = len(points)
    for i, a in enumerate(points):
        b = points[(i + 1) % n]
        steps = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / spacing)))
        for k in range(steps):
            f = k / steps
            dense.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return dense


def union(shapes):
    result = shapes[0]
    for s in shapes[1:]:
        result = result + s
    return result


class RootSide:
    """Measured skin beside one fin side: root edge, land, crease, facet.

    centre_x / half_span set the axial window used to confirm the crease line is
    straight (checked at the two ends and the middle). `side` is +1 / -1 for the
    +tangent / -tangent side of the blade.
    """

    def __init__(self, crop, fin, clock, side, centre_x, half_span=10.0,
                 edge_search=8.0, crease_search=12.0):
        self.crop, self.fin, self.clock, self.side = crop, fin, clock, side
        self.centre_x = centre_x
        self.edge_search, self.crease_search = edge_search, crease_search
        self.radial, self.tangent = clock_frame(clock)
        self.axis = bd.Vector(1.0, 0.0, 0.0)
        self._edge = {}
        self.crease_ends = {x: self._crease_abs(x) for x in (centre_x - half_span,
                                                           centre_x + half_span)}
        mid = self._crease_abs(centre_x)
        if abs(mid - self.crease_t(centre_x)) > 0.02:
            raise ValueError(("crease line is not straight", clock, side, mid,
                              self.crease_t(centre_x)))

    def hit(self, x, t_abs):
        return skin_point(self.crop, x, self.side * t_abs, self.clock)

    def edge(self, x):
        key = round(x, 6)
        if key not in self._edge:
            def outside(t):
                h = self.hit(x, t)
                return not self.fin.is_inside(h["point"] + h["normal"] * 0.05)
            if outside(0.0) or not outside(self.edge_search):
                raise ValueError(("root edge not bracketed", x, self.clock, self.side))
            self._edge[key] = bisect(outside, 0.0, self.edge_search)
        return self._edge[key]

    def _crease_abs(self, x):
        e = self.edge(x)
        n0 = self.hit(x, e + 0.5)["normal"]
        turned = lambda t: self.hit(x, t)["normal"].dot(n0) < 0.99
        if turned(e + 1.0) or not turned(e + self.crease_search):
            raise ValueError(("crease not bracketed", x, self.clock, self.side))
        return bisect(turned, e + 1.0, e + self.crease_search)

    def crease_t(self, x):
        (x0, c0), (x1, c1) = sorted(self.crease_ends.items())
        return c0 + (c1 - c0) * (x - x0) / (x1 - x0)

    def crease_w(self, x):
        return self.crease_t(x) - self.edge(x)

    def _dir(self, normal):
        d = self.axis.cross(normal).normalized()
        return d if d.dot(self.tangent * self.side) > 0.0 else -d

    def point(self, u, w):
        """3D skin point at axial offset u from `centre_x` and arc distance w from the root edge.

        The land is planar; the facet is planar per section.
        """
        x = self.centre_x + u
        e, tc = self.edge(x), self.crease_t(x)
        land = self.hit(x, (e + tc) / 2.0)
        n0 = land["normal"]
        root = self.hit(x, e)["point"]
        wc = tc - e
        if w <= wc:
            return root + self._dir(n0) * w
        crease = root + self._dir(n0) * wc
        n1 = self.hit(x, tc + 1.5)["normal"]
        return crease + self._dir(n1) * (w - wc)


def local_crop_box(clock, x_range, t_range, r_range):
    """Box in the clock's local frame (Y = tangent offset, Z = radial) rotated to `clock`."""
    (x0, x1), (t0, t1), (r0, r1) = x_range, t_range, r_range
    box = bd.Box(x1 - x0, t1 - t0, r1 - r0)
    box = box.translate(((x0 + x1) / 2.0, (t0 + t1) / 2.0, (r0 + r1) / 2.0))
    return box.rotate(bd.Axis.X, -clock)


def blade_faces(fin, clock, min_top=150.0, minimum=4):
    """Faces of a fin whose outer radial extent exceeds `min_top` (the blade, not the root)."""
    radial, _ = clock_frame(clock)
    out = []
    for f in fin.faces():
        bb = f.bounding_box()
        top = max(bd.Vector(0, y, z).dot(radial) for y in (bb.min.Y, bb.max.Y)
                  for z in (bb.min.Z, bb.max.Z))
        if top > min_top:
            out.append(f)
    if len(out) < minimum:
        raise ValueError(("blade faces not found", clock, len(out)))
    return out
