"""B2E: B2D with the ramp deployed a further 15 mm of tangential lip travel (35 -> ~50 mm drop, 3.04 -> 4.342 deg).

B2 detail pass (surface-visible features only; internals stay undetailed). Visual concept, not approved geometry.

Scope chosen by the user 2026-09-28: intake face + door, rear nozzle (round petals, O1 style), ramp/engine mount.
Builds on the rough B2 layout in `engine_bay_b2.py` (engine 575 mm envelope at X-897..-322 riding on the ramp,
340 mm forward-hinged door, straight bypass duct). The rough B2 STEPs stay untouched as comparison evidence.
Differences from rough B2: belly opening is now a 1 mm seam around the door over a larger hidden chamber; the
duct end is 96 x 84 (fits inside the 90 mm-tall engine). Coordinates mm, +X forward, +Y starboard, +Z dorsal.
"""

from __future__ import annotations

import math
from pathlib import Path

from cadgen import build123d as bd, srgb, step

import aft_exhaust_r1 as aft
import engine_bay_b2 as b
import engine_read_study as e

HINGE_X, HINGE_Z = -950.0, -83.0            # real R1/R3 ramp hinge (rough B2 used (-951,-86), ~3 mm off in Z)
RAMP_LEVER = math.hypot(660.0, 3.0)         # hinge-to-lip distance used by R3 for the 35 mm setting
RAMP_DEG_R3 = b.RAMP_DEG                    # 3.0402 deg = saved R3 Deployed pose
RAMP_DEG = RAMP_DEG_R3 + math.degrees(15.0 / RAMP_LEVER)   # +15 mm tangential lip travel = 4.3424 deg


def pose(shape, deg):
    return shape.rotate(bd.Axis(origin=(HINGE_X, 0.0, HINGE_Z), direction=(0, 1, 0)), deg)


def read_state(state):
    parts = aft._read_parts(state)
    if state == "Deployed":
        ramp = parts["intake_r1_ramp"]
        moved = ramp.rotate(bd.Axis((HINGE_X, 0.0, HINGE_Z), (0, 1, 0)), RAMP_DEG - RAMP_DEG_R3)
        moved.label, moved.color = ramp.label, ramp.color
        parts["intake_r1_ramp"] = moved
    return parts

ROOT = Path(__file__).resolve().parents[1]
ENGINE_Z0 = -82.9                             # 0.1 mm above the ramp plate top (rough B2 had -83.0 and touched/penetrated by ~0.05 mm when deployed)
Z_C = ENGINE_Z0 + b.ENGINE_H / 2.0            # engine axis height (stowed frame)
XF = b.ENGINE_X[1]                            # engine front face X (stowed frame)
CHAMBER = (b.POCKET[0], b.POCKET[1], -83.0, -20.0)  # X0, X1, Z0, Z1 (hidden chamber above the door)
SEAM = 1.0                                    # belly-skin clearance around the door
PANEL = srgb("#5a6875")
TRIM = srgb("#3d4650")
PETAL = e.METAL


def engine_envelope(deg):
    length = b.ENGINE_X[1] - b.ENGINE_X[0]
    block = bd.Box(length, b.ENGINE_W, b.ENGINE_H).translate(((b.ENGINE_X[0] + b.ENGINE_X[1]) / 2.0, 0.0, Z_C))
    block.label, block.color = "b2_engine_envelope", b.ENGINE_COLOR
    return pose(block, deg)


def engine_cavity():
    """Internal cavity swept by the envelope (stowed/mid/deployed union, +1.5 mm) extended 30 mm forward for the intake face parts."""
    x0, x1 = b.ENGINE_X[0] - 1.5, b.ENGINE_X[1] + 30.0
    base = bd.Box(x1 - x0, b.ENGINE_W + 3.0, b.ENGINE_H + 3.0).translate(((x0 + x1) / 2.0, 0.0, Z_C))
    cav = base
    for deg in (RAMP_DEG / 2.0, RAMP_DEG):
        cav = cav + pose(base, deg)
    return cav.clean()


def bypass_duct():
    return aft.ruled_loft(((-1310.0, 84.0, 84.0, 0.0, 8.0), (b.ENGINE_X[0], 96.0, 84.0, Z_C, 8.0)))


def door_cutters():
    """Hidden chamber above the door plus a seam-width aperture through the belly skin."""
    chamber = bd.Box(CHAMBER[1] - CHAMBER[0], 124.0, CHAMBER[3] - CHAMBER[2]).translate(
        ((CHAMBER[0] + CHAMBER[1]) / 2.0, 0.0, (CHAMBER[2] + CHAMBER[3]) / 2.0))
    ax0 = b.DOOR_HINGE[0] - b.DOOR_LEN - SEAM
    ax1 = b.DOOR_HINGE[0] + 4.0  # forward end leaves room for the hinge barrels (radius 2.5)
    aperture = bd.Box(ax1 - ax0, b.DOOR_W + 2 * SEAM, 7.0).translate(((ax0 + ax1) / 2.0, 0.0, -85.0))  # Z-88.5..-81.5
    return (chamber + aperture).clean()


def cutters():
    return (aft.seat_cutter() + bypass_duct() + engine_cavity() + door_cutters()).clean()


def body_cut(state):
    """Review-copy body: clipped R3 body minus rear seat, straight duct, engine sweep cavity, door chamber/aperture."""
    parts = read_state(state)
    clip = bd.Box(1500.0, 500.0, 500.0).translate((-650.0, 250.0, 0.0))
    body = parts[aft.BODY_LABEL] & clip
    return (body - cutters()).clean(), parts, clip


# ---------------------------------------------------------------- intake face
def intake_parts(deg):
    L = e.label
    out = []
    frame = aft.ruled_loft(((XF, b.ENGINE_W, b.ENGINE_H, Z_C, 10.0), (XF + 3.0, b.ENGINE_W, b.ENGINE_H, Z_C, 10.0))) - \
        aft.ruled_loft(((XF - 1, 96.0, 76.0, Z_C, 8.0), (XF + 4.0, 96.0, 76.0, Z_C, 8.0)))
    out.append(L(frame.clean(), "b2d_face_frame", PANEL))
    lip = e._cone(XF + 2.0, XF + 9.0, 44.5, 41.5, 0.0, Z_C) - e._cone(XF + 1.9, XF + 9.1, 42.6, 39.0, 0.0, Z_C)
    out.append(L(lip.clean(), "b2d_inlet_lip", e.METAL))
    out.append(L(e.rotor(XF + 3.0, 38.5, 12.0, 26, 5.0, z=Z_C, pitch=30.0, ring=False), "b2d_fan", e.BLADE))
    out.append(L(e._cone(XF + 5.5, XF + 24.0, 12.0, 1.5, 0.0, Z_C), "b2d_spinner", e.METAL))
    return [pose(p, deg) for p in out]


# ------------------------------------------------------------ ramp/engine mount
def mount_parts(deg):
    L = e.label
    out = []
    for i, x in enumerate((-820.0, -690.0, -560.0, -430.0)):
        for side, sy in (("port", -1), ("stbd", 1)):
            pad = bd.Box(6.0, 2.6, 38.0).translate((x, sy * (b.ENGINE_W / 2.0 + 1.3), ENGINE_Z0 + 19.0))
            out.append(L(pad, f"b2d_mount_pad_{i}_{side}", TRIM))
    return [pose(p, deg) for p in out]


# --------------------------------------------------------------------- door
def door_parts(open_pose):
    L = e.label
    plate = bd.Box(b.DOOR_LEN, b.DOOR_W, b.DOOR_T).translate((-b.DOOR_LEN / 2.0, 0.0, 0.0))
    plate = L(plate, "b2d_door_panel", b.DOOR_COLOR)
    t2 = b.DOOR_T / 2.0
    outer = bd.Box(b.DOOR_LEN - 2.0, b.DOOR_W - 2.0, 3.0)
    inner = bd.Box(b.DOOR_LEN - 10.0, b.DOOR_W - 10.0, 4.0)
    rim = (outer - inner).translate((-b.DOOR_LEN / 2.0, 0.0, t2 + 1.5))
    ribs = [bd.Box(2.0, b.DOOR_W - 8.0, 3.0).translate((-x, 0.0, t2 + 1.5)) for x in (85.0, 170.0, 255.0)]
    for r_ in ribs:
        rim = rim + r_
    frame = L(rim.clean(), "b2d_door_frame", TRIM)
    barrels = None
    for sy in (-1, 1):
        for k in range(3):
            bar = bd.Cylinder(2.5, 8.0, rotation=(90, 0, 0)).translate((0.0, sy * (52.0 - 12.0 * k + 0.0), 0.0))
            barrels = bar if barrels is None else barrels + bar
    barrels = barrels + bd.Cylinder(1.2, 2 * 58.5, rotation=(90, 0, 0))
    barrels = L(barrels.clean(), "b2d_door_hinge", TRIM)
    out = []
    for p in (plate, frame, barrels):
        q = p.rotate(bd.Axis.Y, b.DOOR_OPEN_DEG) if open_pose else p
        q = q.translate((b.DOOR_HINGE[0], 0.0, b.DOOR_HINGE[1]))
        q.label, q.color = p.label, p.color
        out.append(q)
    return out


# ------------------------------------------------------------------- nozzle
def nozzle_parts():
    L = e.label
    out = []
    ring = e.cyl_x(-1354.0, -1351.0, 49.5) - e.cyl_x(-1355.0, -1350.0, 43.5)
    out.append(L(ring.clean(), "b2d_nozzle_ring", TRIM))
    for i, p in enumerate(e.petals_round(-1391.0, -1352.0, 52.0, 44.0, 12)):
        out.append(L(p, f"b2d_nozzle_petal_{i}", PETAL))
    out.append(L(e._cone(-1340.0, -1372.0, 10.0, 1.0, 0.0, 0.0), "b2d_tail_cone", e.HOT))
    for ang in (45, 135, 225, 315):
        dy, dz = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        wall = e.liner_half(-1345.0)
        out.append(L(e.strut_across(-1345.0, dy * 6.0, dz * 6.0, dy * wall * 0.96, dz * wall * 0.96, 2.0, 5.0, 1.5), f"b2d_tail_strut_{ang}", TRIM))
    return out


def detail_parts(state):
    deg = RAMP_DEG if state == "Deployed" else 0.0
    return ([engine_envelope(deg)] + intake_parts(deg) + mount_parts(deg) + door_parts(state == "Deployed") + nozzle_parts())


def context(state):
    body, parts, clip = body_cut(state)
    body.label, body.color = aft.BODY_LABEL + "_SECTION_REVIEW_ONLY", parts[aft.BODY_LABEL].color
    out = [body]
    for label, part in parts.items():
        if label == aft.BODY_LABEL:
            continue
        c = part & clip
        if c is not None and c.volume > 1e-4:
            c.label, c.color = label + "_SECTION_REVIEW_ONLY", part.color
            out.append(c)
    liner = aft.liner() & clip
    liner.label, liner.color = "aft_exhaust_r1_liner_SECTION_REVIEW_ONLY", e.DARK
    out.append(liner)
    for p in detail_parts(state):
        c = p & clip
        if c is not None and c.volume > 1e-4:
            c.label, c.color = p.label, p.color
            out.append(c)
    return bd.Compound(children=out, label=f"S_EngineBay_B2E_{state}")


def full(state):
    """Whole airframe: saved R3 state parts, body with B2D cuts, R1 liner, and all B2D detail parts (no clipping)."""
    parts = read_state(state)
    body = (parts[aft.BODY_LABEL] - cutters()).clean()
    body.label, body.color = aft.BODY_LABEL, parts[aft.BODY_LABEL].color
    out = [body] + [p for k, p in parts.items() if k != aft.BODY_LABEL]
    liner = aft.liner()
    out.append(liner)
    out.extend(detail_parts(state))
    return bd.Compound(children=out, label=f"S_EngineBay_B2E_{state}_Full")


@step(out="../STEP/S_EngineBay_B2E_Deployed_Full.step")
def deployed_full():
    return full("Deployed")


@step(out="../STEP/S_EngineBay_B2E_Stowed_Full.step")
def stowed_full():
    return full("Stowed")


@step(out="../STEP/S_EngineBay_B2E_Deployed_Cutaway.step")
def deployed():
    return context("Deployed")


@step(out="../STEP/S_EngineBay_B2E_Stowed_Cutaway.step")
def stowed():
    return context("Stowed")


if __name__ == "__main__":
    deployed()
    stowed()
    deployed_full()
    stowed_full()
