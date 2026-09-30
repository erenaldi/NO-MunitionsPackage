"""A14: D4 hooded turret stubs on the front, an inset-look window on the rear.

The rear cap (approved A10) is not cut. A raised bezel frame is built on the
tail surface and a thinner lens window is seated inside it, so the lens sits a
few mm below the frame top: (footprint prism ∩ tail offset) − tail, split into
a frame and a window. Cosmetic study geometry only.
"""

from cadgen import build123d as bd

from housing import solid_box
from mounts import build as mount_build
from sensors import shells, stadium_x, tail_offset
from teal_nose import study as base_study

CZ = -111.5
FRAME_T, WINDOW_T = 6., 3.


def rear_window_parts(tail):
    outer = stadium_x(0, CZ, 130., 66., -1740., -1490.)
    inner = stadium_x(0, CZ, 100., 40., -1740., -1490.)
    frame_skin = (outer & tail_offset(FRAME_T)) - tail
    frame = frame_skin - (inner & tail_offset(FRAME_T+1))
    window = (inner & tail_offset(WINDOW_T)) - tail
    frame.label, window.label = "sensor_rear_window_frame", "sensor_rear_window_lens"
    parts = []
    for part in (frame, window):
        pieces = [p for p in part.solids() if p.volume > 3]
        assert pieces, (part.label, "empty")
        for i, piece in enumerate(pieces):
            piece.label = part.label + (f"_{i+1}" if len(pieces) > 1 else "")
            parts.append(piece)
    return parts


def build():
    _, tail = shells()
    return mount_build("D4", ends=("front",)) + rear_window_parts(tail)


def study():
    return bd.Compound(children=list(base_study(False).children)+build())


def crop_rear():
    _, tail = shells()
    tail.label = "shell"
    stub = solid_box("beam_stub", 120, 400, 223, (-1265, 0, -111.5))
    return bd.Compound(children=[tail, stub]+rear_window_parts(tail))
