"""B2H: square rear nozzle (user choice 2026-09-29) replacing the B2G round-petal ring, which left dark gaps in the
rounded-square opening's corners. Fictional game asset; visual only.

The nozzle is a chamfered-square (octagonal) flap ring lining the flaring rounded-square liner at ~2.6 mm inset:
4 tapered side flaps + 4 narrow corner facets with 0.6 mm seams, engraved centre lines, and a rounded-square mount
ring whose outer edge embeds in the liner wall. Round tail cone, shaft and turbine stage are reused from B2G.
Everything else in B2F/B2G is unchanged. Coordinates mm, +X forward, +Y starboard, +Z dorsal.
"""

from __future__ import annotations

import math
from pathlib import Path

from cadgen import build123d as bd, srgb, step

import aft_exhaust_r1 as aft
import engine_bay_b2g as g
import engine_bay_cosmetic as c
import engine_read_study as e

ROOT = Path(__file__).resolve().parents[1]
INSET = 2.6
CHAMFER = 9.0          # leg of the corner chamfer on the flap octagon
GAP = 1.0              # seam between flaps
T = 1.6
X_AFT, X_FWD = -1391.0, -1352.0
RING_X = (-1355.0, -1349.0)
STRUT_X = -1347.5
SIDE_COLOR = srgb("#9aa5b1")
FACET_COLOR = srgb("#7d8996")
TRIM = g.TRIM
KEEP_FROM_B2G = ("b2g_tail_cone", "b2g_tail_shaft", "b2g_turbine_stage")


def _plate(rm, tilt_deg, length, w_tip, w_root, rot_deg, label, color, ring):
    pts = [(-length / 2, -w_tip / 2), (length / 2, -w_root / 2), (length / 2, w_root / 2), (-length / 2, w_tip / 2)]
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, 0.0) for x, y in pts], close=True))
    body = bd.Solid.extrude(face, bd.Vector(0.0, 0.0, T)).translate((0.0, 0.0, -T / 2))
    zi = -T / 2
    tools = [bd.Box(length - 10.0, 0.6, 0.9).translate((-2.0, 0.0, zi + (0.4 - 0.5) / 2))]
    if ring:
        tools.append((bd.Cylinder(1.7, 0.9) - bd.Cylinder(1.0, 2.0)).translate((length / 2 - 7.0, 0.0, zi + (0.4 - 0.5) / 2)))
    for t in tools:
        body = (body - t).clean()
    body = body.rotate(bd.Axis.Y, tilt_deg)
    body = bd.Pos((X_AFT + X_FWD) / 2.0, 0.0, rm) * body
    body = body.rotate(bd.Axis.X, rot_deg)
    body.label, body.color = label, color
    return body


def flaps():
    a_e = e.liner_half(X_AFT) - INSET
    a_f = e.liner_half(X_FWD) - INSET
    span = X_FWD - X_AFT
    out = []
    # side flaps: plane at distance a, tapered because the flat spans |y| <= a - CHAMFER
    L_s = math.hypot(span, a_e - a_f)
    tilt_s = math.degrees(math.atan2(a_e - a_f, span))
    for k, name in enumerate(("dorsal", "starboard", "ventral", "port")):
        out.append(_plate((a_e + a_f) / 2.0, tilt_s, L_s, 2 * (a_e - CHAMFER) - GAP, 2 * (a_f - CHAMFER) - GAP,
                          90.0 * k, f"b2h_nozzle_flap_{name}", SIDE_COLOR, True))
    # corner facets: plane at 45 deg, distance b = (2a - CHAMFER)/sqrt2
    b_e = (2 * a_e - CHAMFER) / math.sqrt(2)
    b_f = (2 * a_f - CHAMFER) / math.sqrt(2)
    L_f = math.hypot(span, b_e - b_f)
    tilt_f = math.degrees(math.atan2(b_e - b_f, span))
    w_f = CHAMFER * math.sqrt(2) - GAP
    for k, name in enumerate(("dorsal_starboard", "starboard_ventral", "ventral_port", "port_dorsal")):
        out.append(_plate((b_e + b_f) / 2.0, tilt_f, L_f, w_f, w_f, 45.0 + 90.0 * k,
                          f"b2h_nozzle_facet_{name}", FACET_COLOR, False))
    return out


def nozzle_parts():
    L = e.label
    out = []
    def _outer(x):
        half = e.liner_half(x) + 0.3
        rad = 8.0 - 2.0 * (x + 1360.0) / 50.0 + 0.3     # liner corner radius interpolated from (-1360: 8) to (-1310: 6), +0.3 embed
        return (x, 2 * half, 2 * half, 0.0, rad)

    ring = aft.ruled_loft((_outer(RING_X[0]), _outer(RING_X[1]))) -         aft.ruled_loft(((RING_X[0] - 1.0, 84.0, 84.0, 0.0, 4.0), (RING_X[1] + 1.0, 84.0, 84.0, 0.0, 4.0)))
    out.append(L(ring.clean(), "b2h_nozzle_ring", TRIM))
    out.extend(flaps())
    for ang in (45, 135, 225, 315):
        dy, dz = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        out.append(L(e.strut_across(STRUT_X, dy * 5.0, dz * 5.0, dy * 60.0, dz * 60.0, 2.6, 5.0, 0.0), f"b2h_tail_strut_{ang}", TRIM))
    out.extend(p for p in g.nozzle_parts() if p.label in KEEP_FROM_B2G)
    return out


def full(state):
    base = c.full(state)
    kids = [k for k in base.children if not str(k.label).startswith(("b2d_nozzle", "b2d_tail"))]
    return bd.Compound(children=kids + nozzle_parts(), label=f"S_EngineBay_B2H_{state}_Full")


@step(out="../STEP/S_EngineBay_B2H_Deployed_Full.step")
def deployed_full():
    return full("Deployed")


@step(out="../STEP/S_EngineBay_B2H_Stowed_Full.step")
def stowed_full():
    return full("Stowed")


@step(out="../STEP/S_Nozzle_B2H_Section.step")
def nozzle_section():
    clip = bd.Box(400.0, 300.0, 300.0).translate((-1250.0, 150.0, 0.0))
    kids = []
    for p in [aft.liner()] + nozzle_parts():
        q = p & clip
        if q is not None and q.volume > 1e-4:
            q.label, q.color = str(p.label) + "_SECTION_REVIEW_ONLY", p.color
            kids.append(q)
    return bd.Compound(children=kids, label="Nozzle_B2H_Section_Review")


if __name__ == "__main__":
    nozzle_section()
    deployed_full()
    stowed_full()
