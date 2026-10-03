"""Cut details into short axial sections of a long host, not into the whole body.

Why (Codex audit + our R20/R21 numbers): every Boolean on a long host pays for all of
its faces, and each detail cut adds faces to it, so N sequential cuts on one body get
slower as it grows (R19: average cut 0.55 s -> 1.22 s over 165 cuts; R21 took the
booster body from 416 to 2,240 faces). Splitting the host once into sections, cutting
each detail into the single section that contains it, and only then rejoining keeps
every Boolean small and the face count local.

Boundaries should sit on intentional seams (ring seams, stage splits) when the sections
stay separate leaves; for a rejoined host any X plane works because `rejoin` fuses.

Nothing runs at import time.
"""
from __future__ import annotations

import time

from cadgen import build123d as bd

from surface_detail import checked_cut


class Section:
    def __init__(self, x0, x1, shape):
        self.x0, self.x1, self.shape = x0, x1, shape

    @property
    def faces(self):
        return len(self.shape.faces())


def _box(x0, x1, half):
    return bd.Box(x1 - x0, 2 * half, 2 * half).translate(((x0 + x1) / 2.0, 0.0, 0.0))


def split_host(host, boundaries, half=1000.0):
    """Split `host` at the X planes in `boundaries` (ascending). Returns [Section]."""
    bb = host.bounding_box()
    edges = [bb.min.X - 1.0] + sorted(boundaries) + [bb.max.X + 1.0]
    out = []
    for x0, x1 in zip(edges[:-1], edges[1:]):
        piece = host & _box(x0, x1, half)
        if piece is None or not piece.solids():
            raise ValueError(("empty section", x0, x1))
        out.append(Section(x0, x1, piece))
    return out


def section_of(sections, cutter, margin=0.5):
    """Index of the one section containing `cutter` (bbox) with `margin`, else ValueError."""
    cb = cutter.bounding_box()
    for i, s in enumerate(sections):
        if cb.min.X >= s.x0 + margin and cb.max.X <= s.x1 - margin:
            return i
    raise ValueError(("cutter straddles a section boundary", cb.min.X, cb.max.X))


def apply_cuts(sections, cutters, minimum=1e-3):
    """Apply each cutter to its section with `checked_cut`. Returns per-cut timing rows.

    Each row: (index, section, seconds, faces_after). Sections are updated in place.
    """
    rows = []
    for k, cutter in enumerate(cutters):
        i = section_of(sections, cutter)
        t = time.time()
        sections[i].shape = checked_cut(sections[i].shape, cutter, minimum)
        rows.append((k, i, time.time() - t, sections[i].faces))
    return rows


def rejoin(sections):
    """Fuse the sections back into one solid (clean). One Boolean chain, done once."""
    result = sections[0].shape
    for s in sections[1:]:
        result = result + s.shape
    return result.clean() if hasattr(result, "clean") else result


def face_report(sections):
    return [{"x0": round(s.x0, 1), "x1": round(s.x1, 1), "faces": s.faces} for s in sections]


def choose_boundaries(cutters, x_min, x_max, target_len=250.0, margin=0.5):
    """Split planes near every `target_len` that no cutter crosses (so none straddles).

    For each ideal position the nearest X that lies outside every cutter's [min-margin, max+margin]
    X interval is used; positions with no free X within half a section are skipped (fewer sections).
    """
    spans = sorted((c.bounding_box().min.X - margin, c.bounding_box().max.X + margin) for c in cutters)
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])

    def free(x):
        return not any(a <= x <= b for a, b in merged)

    def nearest_free(x, reach):
        if free(x):
            return x
        step = 0.5
        d = step
        while d <= reach:
            for cand in (x - d, x + d):
                if free(cand):
                    return cand
            d += step
        return None

    out, n = [], 1
    while x_min + n * target_len < x_max - target_len / 2.0:
        cand = nearest_free(x_min + n * target_len, target_len / 2.0)
        if cand is not None and (not out or cand - out[-1] > target_len / 4.0):
            out.append(round(cand, 3))
        n += 1
    return out
