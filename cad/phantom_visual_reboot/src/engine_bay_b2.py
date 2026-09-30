"""Rough concept study B2, from the user's sketch (2026-09-28): engine carried on the main ramp, straight bypass
duct to the nozzle, longer forward-hinged second door. Surface-only fidelity: the engine is a plain envelope block
with a simple fan face; internals are not modelled. Visual concept only.

Sketch scale recovered from the annotated image: ~1.305 px/mm, X-1400 at px 93, Z0 at px 527.5.
  red   engine envelope: ~575 long x ~90 tall, tilted with the deployed ramp (3.04 deg nose down)
  teal  mounting: the existing ramp plate under the engine
  green straight taper duct from the engine aft face to the nozzle (84 x 84 at X-1310)
  purple second door: hinge X-117 Z-84.5, closed length ~170, open ~19 deg reaching Z~-26 at X-286
Coordinates mm, +X forward, +Y starboard, +Z dorsal. R1 files are untouched; cuts appear only in clipped review copies.
"""

from __future__ import annotations

import math
from pathlib import Path

from cadgen import build123d as bd, srgb, step

import aft_exhaust_r1 as aft
import engine_read_study as e

ROOT = Path(__file__).resolve().parents[1]
BODY = aft.BODY_LABEL

HINGE = (-951.0, -86.0)        # ramp aft hinge (X, Z), from deployed vs stowed plate heights
RAMP_DEG = 3.0402055           # R3 deployment angle for the accepted 35 mm lip drop
ENGINE_X = (-897.0, -322.0)    # stowed-frame length 575; moved +50 mm forward at user request
ENGINE_Z0 = -83.0              # sits on the 3 mm ramp plate (top at -83 stowed)
ENGINE_H = 90.0
ENGINE_W = 112.0
DOOR_LEN, DOOR_W, DOOR_T = 340.0, 116.0, 3.0
DOOR_HINGE = (53.0, -84.5)     # aft edge kept at X-287 (abuts the ramp); hinge moved forward
DOOR_OPEN_DEG = 9.86           # keeps the sketched aft-edge height (Z~-26)
POCKET = (-292.0, 58.0)      # X range of proposed door pocket
ENGINE_COLOR = srgb("#7d8791")
DOOR_COLOR = srgb("#6d7f8f")


def pose(shape, deg):
    """Rotate with the ramp about its aft hinge (+Y rotation lowers the forward end)."""
    return shape.rotate(bd.Axis(origin=(HINGE[0], 0.0, HINGE[1]), direction=(0, 1, 0)), deg)


def engine_block(deg):
    length = ENGINE_X[1] - ENGINE_X[0]
    block = bd.Box(length, ENGINE_W, ENGINE_H).translate(((ENGINE_X[0] + ENGINE_X[1]) / 2.0, 0.0, ENGINE_Z0 + ENGINE_H / 2.0))
    block.label, block.color = "b2_engine_envelope", ENGINE_COLOR
    fan = e.rotor(ENGINE_X[1] - 3.0, 40.0, 12.0, 24, 6.0, z=ENGINE_Z0 + ENGINE_H / 2.0)
    fan.label, fan.color = "b2_fan_face", e.BLADE
    return [pose(block, deg), pose(fan, deg)]


def engine_cavity():
    """Internal cavity swept by the engine block between stowed and deployed (union of three poses, +1.5 mm)."""
    length = ENGINE_X[1] - ENGINE_X[0] + 3.0
    base = bd.Box(length, ENGINE_W + 3.0, ENGINE_H + 3.0).translate(((ENGINE_X[0] + ENGINE_X[1]) / 2.0, 0.0, ENGINE_Z0 + ENGINE_H / 2.0))
    cav = base
    for d in (RAMP_DEG / 2.0, RAMP_DEG):
        cav = cav + pose(base, d)
    return cav.clean()


def bypass_duct():
    return aft.ruled_loft(((-1310.0, 84.0, 84.0, 0.0, 8.0), (ENGINE_X[0], 100.0, 90.0, ENGINE_Z0 + ENGINE_H / 2.0, 8.0)))


def pocket_cutter():
    box = bd.Box(POCKET[1] - POCKET[0], 124.0, 68.0)
    return box.translate(((POCKET[0] + POCKET[1]) / 2.0, 0.0, -54.0))  # Z-88..-20


def door(open_pose):
    plate = bd.Box(DOOR_LEN, DOOR_W, DOOR_T).translate((-DOOR_LEN / 2.0, 0.0, 0.0))
    for sy in (-1, 1):
        plate = plate + bd.Cylinder(2.5, 6.0, rotation=(90, 0, 0)).translate((0.0, sy * (DOOR_W / 2.0 + 1.0), 0.0))
    plate = plate.clean()
    if open_pose:
        plate = plate.rotate(bd.Axis.Y, DOOR_OPEN_DEG)
    plate = plate.translate((DOOR_HINGE[0], 0.0, DOOR_HINGE[1]))
    plate.label, plate.color = ("b2_door_open" if open_pose else "b2_door_closed"), DOOR_COLOR
    return plate


def context(state):
    """Clip the saved R3 state (no R1 exhaust cuts) to a port-open half-section and apply the B2 review-only cuts."""
    parts = aft._read_parts(state)
    clip = bd.Box(1500.0, 500.0, 500.0).translate((-650.0, 250.0, 0.0))
    cutters = (aft.seat_cutter() + bypass_duct() + engine_cavity() + pocket_cutter()).clean()
    out = []
    for label, part in parts.items():
        c = part & clip
        if c is None or c.volume <= 1e-4:
            continue
        if label == BODY:
            c = (c - cutters).clean()
        c.label = label + "_SECTION_REVIEW_ONLY"
        c.color = part.color
        out.append(c)
    liner = aft.liner() & clip
    liner.label, liner.color = "aft_exhaust_r1_liner_SECTION_REVIEW_ONLY", e.DARK
    out.append(liner)
    deg = RAMP_DEG if state == "Deployed" else 0.0
    for p in engine_block(deg) + [door(state == "Deployed")]:
        c = p & clip
        if c is not None and c.volume > 1e-4:
            c.label, c.color = p.label, p.color
            out.append(c)
    return bd.Compound(children=out, label=f"S_EngineBay_B2_{state}")


@step(out="../STEP/S_EngineBay_B2_Deployed_Cutaway.step")
def deployed():
    return context("Deployed")


@step(out="../STEP/S_EngineBay_B2_Stowed_Cutaway.step")
def stowed():
    return context("Stowed")


if __name__ == "__main__":
    deployed()
    stowed()
