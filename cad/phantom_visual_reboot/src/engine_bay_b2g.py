"""B2G: rear-nozzle fixes after the 2026-09-29 design review of B2F (fictional game asset; visual only).

Changes vs B2F nozzle (everything else in B2F is reused unchanged):
  1. Tail cone assembly is now attached: struts sit in the ring plane and end inside the ring; a short tail shaft joins
     the cone to a visible turbine stage whose rim embeds in the liner wall.
  2. Petals are tapered trapezoids (wider at the exit) in alternating master/slave layers so adjacent petals overlap
     without touching; each has an engraved centre line and a fastener ring on the inner face.
  3. A turbine stage gives the view down the nozzle a focal detail (replaces the bare flat wall).
  4. Trim colour lightened so ring/struts read against the black liner.
Petals flare outward toward the exit (r44 forward -> r52 at the exit); earlier notes called this 'converging' in error.
Coordinates mm, +X forward, +Y starboard, +Z dorsal.
"""

from __future__ import annotations

import math
from pathlib import Path

from cadgen import build123d as bd, srgb, step

import aft_exhaust_r1 as aft
import engine_bay_b2e as d
import engine_bay_cosmetic as c
import engine_read_study as e

ROOT = Path(__file__).resolve().parents[1]
TRIM = srgb("#8b96a3")
PETAL_M = srgb("#9aa5b1")
PETAL_S = srgb("#7d8996")
X_AFT, X_FWD = -1391.0, -1352.0
R_AFT, R_FWD = 52.0, 44.0
T = 1.6
COUNT = 12
SLAVE_INSET = 2.6            # radial inset of slave petals (must exceed T to clear the masters)
RING_X = (-1354.0, -1351.0)
ROTOR_X = -1322.0
NOZZLE_PREFIXES = ("b2d_nozzle", "b2d_tail")


def petal(master: bool, index: int):
    span = X_FWD - X_AFT
    ang = math.degrees(math.atan2(R_AFT - R_FWD, span))
    length = math.hypot(span, R_AFT - R_FWD)
    w_tip, w_root = (30.0, 22.0) if master else (26.0, 20.0)
    pts = [(-length / 2, -w_tip / 2), (length / 2, -w_root / 2), (length / 2, w_root / 2), (-length / 2, w_tip / 2)]
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, 0.0) for x, y in pts], close=True))
    body = bd.Solid.extrude(face, bd.Vector(0.0, 0.0, T)).translate((0.0, 0.0, -T / 2))
    zi = -T / 2                                            # inner (axis-facing) face
    cut = [bd.Box(length - 10.0, 0.6, 0.9).translate((-2.0, 0.0, zi + (0.4 - 0.5) / 2))]
    ringcut = (bd.Cylinder(1.7, 0.9) - bd.Cylinder(1.0, 2.0)).translate((length / 2 - 7.0, 0.0, zi + (0.4 - 0.5) / 2))
    cut.append(ringcut)
    for t in cut:
        body = (body - t).clean()
    rm = (R_AFT + R_FWD) / 2.0 - (0.0 if master else SLAVE_INSET)
    body = body.rotate(bd.Axis.Y, ang)
    body = bd.Pos((X_AFT + X_FWD) / 2.0, 0.0, rm) * body
    body = body.rotate(bd.Axis.X, 360.0 * index / COUNT)
    body.label = f"b2g_nozzle_{'master' if master else 'slave'}_petal_{index}"
    body.color = PETAL_M if master else PETAL_S
    return body


def nozzle_parts():
    L = e.label
    out = []
    ring = e.cyl_x(RING_X[0], RING_X[1], 49.5) - e.cyl_x(RING_X[0] - 1, RING_X[1] + 1, 43.5)
    out.append(L(ring.clean(), "b2g_nozzle_ring", TRIM))
    for i in range(COUNT):
        out.append(petal(i % 2 == 0, i))
    out.append(L(e._cone(-1340.0, -1372.0, 10.0, 1.0, 0.0, 0.0), "b2g_tail_cone", e.HOT))
    xs = (RING_X[0] + RING_X[1]) / 2.0
    for ang in (45, 135, 225, 315):
        dy, dz = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        out.append(L(e.strut_across(xs, dy * 5.0, dz * 5.0, dy * 46.5, dz * 46.5, 2.6, 5.0, 0.0), f"b2g_tail_strut_{ang}", TRIM))
    out.append(L(e.cyl_x(-1341.0, ROTOR_X - 2.0, 5.5), "b2g_tail_shaft", TRIM))
    rot = e.rotor(ROTOR_X, 40.6, 12.0, 24, 5.0, pitch=-25.0, ring=True)
    out.append(L(rot, "b2g_turbine_stage", e.BLADE))
    return out


def full(state):
    base = c.full(state)
    kids = [k for k in base.children if not str(k.label).startswith(NOZZLE_PREFIXES)]
    full.stats = getattr(c.full, "stats", None)
    return bd.Compound(children=kids + nozzle_parts(), label=f"S_EngineBay_B2G_{state}_Full")


@step(out="../STEP/S_EngineBay_B2G_Deployed_Full.step")
def deployed_full():
    return full("Deployed")


@step(out="../STEP/S_EngineBay_B2G_Stowed_Full.step")
def stowed_full():
    return full("Stowed")


@step(out="../STEP/S_Nozzle_B2G_Section.step")
def nozzle_section():
    """Review-only half section (Y>=0) of the liner and B2G nozzle parts."""
    clip = bd.Box(400.0, 300.0, 300.0).translate((-1250.0, 150.0, 0.0))
    kids = []
    for p in [aft.liner()] + nozzle_parts():
        q = p & clip
        if q is not None and q.volume > 1e-4:
            q.label, q.color = str(p.label) + "_SECTION_REVIEW_ONLY", p.color
            kids.append(q)
    return bd.Compound(children=kids, label="Nozzle_B2G_Section_Review")


if __name__ == "__main__":
    nozzle_section()
    deployed_full()
    stowed_full()
