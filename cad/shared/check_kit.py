"""Shared building blocks for saved-artifact checkers (extracted from the R19-R21 checkers).

Import from a checker with the same `sys.path` line the builders use for
`surface_detail`. Nothing here runs at import time.

Speed rules baked in (lesson from the R21 checker, which never finished in 15 min):
- `Stages` logs flushed elapsed seconds per stage and aborts when a stage or the
  whole run exceeds its budget, so a slow check fails loudly instead of hanging.
- `crop_shape` + `closed_and_clean` on the crop replace whole-body BRepAlgoAPI_Check.
- `ray_skin` takes the nearest crossing over one or many shapes; give it the local
  crop, not the full body.
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

from cadgen import build123d as bd, read_scene


class Stages:
    """Flushed per-stage timing with budgets. `stage("name")` closes the previous stage."""

    def __init__(self, stage_budget_s=180.0, total_budget_s=600.0, out=None):
        self.t0 = time.time()
        self.t_stage = self.t0
        self.name = "start"
        self.stage_budget = stage_budget_s
        self.total_budget = total_budget_s
        self.out = out or sys.stdout
        self.timings = {}

    def stage(self, name):
        now = time.time()
        spent = now - self.t_stage
        self.timings[self.name] = round(spent, 2)
        print(f"[{now - self.t0:7.1f}s] {self.name} took {spent:.1f}s -> {name}",
              file=self.out, flush=True)
        if spent > self.stage_budget:
            raise TimeoutError(f"stage '{self.name}' took {spent:.0f}s > budget {self.stage_budget:.0f}s")
        if now - self.t0 > self.total_budget:
            raise TimeoutError(f"total {now - self.t0:.0f}s > budget {self.total_budget:.0f}s at '{name}'")
        self.name, self.t_stage = name, now

    def done(self):
        self.stage("done")
        return self.timings

    def check(self):
        """Call inside long loops: raises as soon as the current stage is over budget."""
        now = time.time()
        if now - self.t_stage > self.stage_budget:
            raise TimeoutError(f"stage '{self.name}' running {now - self.t_stage:.0f}s > budget {self.stage_budget:.0f}s")


class Report:
    """Collects failures and notes; `exit_code()` is 0 only when nothing failed."""

    def __init__(self):
        self.failures, self.notes = [], {}

    def fail(self, message):
        self.failures.append(message)

    def exit_code(self):
        return 1 if self.failures else 0


def load_leaves(path, report=None):
    """(scene, rows, {label: shape}); duplicate leaf labels are reported."""
    scene = read_scene(Path(path))
    rows = tuple(scene.leaves())
    parts = {row.label: scene.resolve(row.ref).shape() for row in rows}
    if len(parts) != len(rows) and report is not None:
        report.fail(f"{Path(path).name}: duplicate leaf labels")
    return scene, rows, parts


def precise_volume(shape):
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    total = 0.0
    for solid in shape.solids():
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(solid.wrapped, props, 1e-9, True, True)
        total += props.Mass()
    return total


def closed_and_clean(shape):
    """Every shell closed, and BRepAlgoAPI_Check (incl. self-intersection) passes.

    Cost grows steeply with face count: run it on new parts and on a `crop_shape`
    of a big host, not on the whole body.
    """
    from OCP.BRep import BRep_Tool
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
    closed = all(BRep_Tool.IsClosed_s(s.wrapped) for s in shape.shells())
    check = BRepAlgoAPI_Check(shape.wrapped, True, True)
    return closed, check.IsValid()


def box_around(x0, x1, half=400.0):
    """Axis-aligned crop box spanning X x0..x1 and +-half in Y and Z."""
    return bd.Box(x1 - x0, 2 * half, 2 * half).translate(((x0 + x1) / 2.0, 0.0, 0.0))


def crop_shape(shape, box):
    """`shape & box`, or None when empty."""
    out = shape & box
    if out is None or not out.solids() or out.volume < 1e-9:
        return None
    return out


def ray_skin(shapes, point, outward, start=20.0):
    """Outermost crossing on the line through `point` along `-outward`.

    `shapes` is one shape or an iterable of shapes (nearest crossing over all of them).
    Raises ValueError when the ray misses.
    """
    from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
    from OCP.gce import gce_MakeLin
    if hasattr(shapes, "wrapped"):
        shapes = [shapes]
    origin = point + outward * start
    line = gce_MakeLin(bd.Axis(origin, -outward).wrapped).Value()
    ws = []
    for shape in shapes:
        hits = BRepIntCurveSurface_Inter()
        hits.Init(shape.wrapped, line, 1e-7)
        while hits.More():
            if hits.W() >= 0.0:
                ws.append(hits.W())
            hits.Next()
    if not ws:
        raise ValueError("reference skin ray missed")
    return origin - outward * min(ws)


def boxes_near(a, b, margin):
    ba, bb = a.bounding_box(), b.bounding_box()
    return not (ba.min.X - margin > bb.max.X or bb.min.X - margin > ba.max.X or
                ba.min.Y - margin > bb.max.Y or bb.min.Y - margin > ba.max.Y or
                ba.min.Z - margin > bb.max.Z or bb.min.Z - margin > ba.max.Z)


def _box6(shape):
    if isinstance(shape, bd.Vector):
        return (shape.X, shape.Y, shape.Z, shape.X, shape.Y, shape.Z)
    b = shape.bounding_box()
    return (b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z)


def _box_gap(a, b, safety=0.01):
    """Distance between two boxes minus `safety` mm: a lower bound of the shape distance."""
    gx = max(a[0] - b[3], b[0] - a[3], 0.0)
    gy = max(a[1] - b[4], b[1] - a[4], 0.0)
    gz = max(a[2] - b[5], b[2] - a[5], 0.0)
    return max(0.0, math.sqrt(gx * gx + gy * gy + gz * gz) - safety)


def min_distance(ps, qs):
    """Exact `min(p.distance_to(q) for p in ps for q in qs)` without the all-pairs cost.

    `qs` may hold shapes or `bd.Vector` points. Pairs are evaluated in bounding-box-gap
    order and the loop stops once the box gap reaches the best distance found, so only
    nearby pairs pay for `distance_to`. Returns `math.inf` when either list is empty.
    (Halberd R21 checker: all-pairs blade and panel loops never finished in 25+ min;
    pruned they take about 45 s and 28 s per band, same values.)
    """
    pb = [_box6(p) for p in ps]
    qb = [_box6(q) for q in qs]
    pairs = sorted(((_box_gap(pb[i], qb[j]), i, j) for i in range(len(ps)) for j in range(len(qs))),
                   key=lambda t: t[0])
    best = math.inf
    for gap, i, j in pairs:
        if gap >= best:
            break
        best = min(best, _dist(ps[i], qs[j]))
    return best


def _dist(p, q):
    """Distance between two shapes or points (a Vector has no `distance_to`)."""
    p_pt, q_pt = isinstance(p, bd.Vector), isinstance(q, bd.Vector)
    if p_pt and q_pt:
        return (p - q).length
    if p_pt:
        return q.distance_to(p)
    return p.distance_to(q)


def frame(clock_degrees):
    """(outward, tangent) for clock 0 = +Z, 90 = +Y."""
    a = math.radians(clock_degrees)
    return bd.Vector(0, math.sin(a), math.cos(a)), bd.Vector(0, math.cos(a), -math.sin(a))


def leaves_unchanged(ref, parts, skip=(), tol=1e-6, report=None):
    """Labels of `ref` leaves that are missing or whose precise volume or bbox moved.

    `skip` holds hosts that are allowed to change (check them separately with
    `removed_volume`). Returns a list of (label, reason).
    """
    bad = []
    skip = set(skip)
    for label, part in ref.items():
        if label in skip:
            continue
        other = parts.get(label)
        if other is None:
            bad.append((label, "missing"))
            continue
        if abs(part.volume - other.volume) > tol:
            bad.append((label, "volume changed"))
            continue
        a, b = part.bounding_box(), other.bounding_box()
        if any(abs(u - v) > 1e-6 for u, v in zip(
                (a.min.X, a.min.Y, a.min.Z, a.max.X, a.max.Y, a.max.Z),
                (b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z))):
            bad.append((label, "bbox changed"))
    if report is not None:
        for label, reason in bad:
            report.fail(f"{label}: {reason}")
    return bad


def removed_volume(before, after):
    """(removed, gained) precise volumes of `before - after` and `after - before`."""
    lost = before - after
    gain = after - before
    return (precise_volume(lost) if lost else 0.0, precise_volume(gain) if gain else 0.0)
