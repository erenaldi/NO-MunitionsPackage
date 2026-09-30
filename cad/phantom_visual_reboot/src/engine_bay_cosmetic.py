"""B2F: restrained cosmetic surface detailing on the B2E model (fictional game asset; purely visual).

Scope chosen by the user 2026-09-29: door + ramp + engine bay, restrained. Everything here is SUBTRACTIVE (0.4 mm
engraved seams 0.8 mm wide, ring grooves around fastener heads, recessed vent-slot arrays), so no new raised geometry
and no new interference with any accepted part. Detailing is applied to: door outer skin, ramp underside, the belly
surround of the bay+door opening, and the engine intake face frame.
Coordinates mm, +X forward, +Y starboard, +Z dorsal; belly plane Z=-86.
"""

from __future__ import annotations

import math
from pathlib import Path

from cadgen import build123d as bd, step

import aft_exhaust_r1 as aft
import engine_bay_b2 as b
import engine_bay_b2e as d
import engine_read_study as e

ROOT = Path(__file__).resolve().parents[1]
DEPTH = 0.4     # engraving depth
SEAM_W = 0.8    # seam / groove width
OVER = 0.5      # tool overrun outside the surface
RING_IN, RING_OUT = 1.5, 2.3
SLOT_W, SLOT_PITCH = 1.4, 5.0


# ---------------------------------------------------------------- tool builders (surface normal is -Z)
def _slab(cx, cy, lx, ly, z_surf):
    """Box tool covering z_surf-OVER .. z_surf+DEPTH (surface faces -Z, material is at higher Z)."""
    return bd.Box(lx, ly, DEPTH + OVER).translate((cx, cy, z_surf + (DEPTH - OVER) / 2.0))


def rect_ring(x0, x1, y0, y1, z_surf, w=SEAM_W):
    outer = _slab((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, z_surf)
    inner = _slab((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0 - 2 * w, y1 - y0 - 2 * w, z_surf).translate((0, 0, 0))
    return outer - inner


def seam_x(x, y0, y1, z_surf, w=SEAM_W):
    return _slab(x, (y0 + y1) / 2, w, y1 - y0, z_surf)


def seam_y(y, x0, x1, z_surf, w=SEAM_W):
    return _slab((x0 + x1) / 2, y, x1 - x0, w, z_surf)


def ring(cx, cy, z_surf):
    h = DEPTH + OVER
    tool = bd.Cylinder(RING_OUT, h) - bd.Cylinder(RING_IN, h + 1.0)
    return tool.translate((cx, cy, z_surf + (DEPTH - OVER) / 2.0))


def slots_y(cx, cy, n, length, z_surf):
    """n slots with long axis along Y, stacked along X at SLOT_PITCH."""
    out = []
    for i in range(n):
        out.append(_slab(cx + (i - (n - 1) / 2.0) * SLOT_PITCH, cy, SLOT_W, length, z_surf))
    return out


def slots_x(cx, cy, n, length, z_surf):
    out = []
    for i in range(n):
        out.append(_slab(cx, cy + (i - (n - 1) / 2.0) * SLOT_PITCH, length, SLOT_W, z_surf))
    return out


def fuse(tools):
    result = tools[0]
    for t in tools[1:]:
        result = result + t
    return result.clean()


def engrave(part, tools, label, color):
    solid = (part - fuse(tools)).clean()
    solid.label, solid.color = label, color
    return solid


def removed(part, tools):
    """Volume of `part` inside the fused tools (= material engraved away)."""
    inter = part & fuse(tools)
    return 0.0 if inter is None else sum(s.volume for s in inter.solids())


def expected(tools, depth_frac=DEPTH / (DEPTH + OVER)):
    return sum(t.volume for t in tools) * depth_frac


# ---------------------------------------------------------------------------------------- door skin
def door_tools():
    zs = -b.DOOR_T / 2.0                       # outer (belly-facing) face in the door's local frame
    L = b.DOOR_LEN
    t = [rect_ring(-L + 5.0, -5.0, -53.0, 53.0, zs)]
    for x in (-L / 3.0, -2.0 * L / 3.0):
        t.append(seam_x(x, -52.6, 52.6, zs))
    for x in range(-20, -321, -50):
        for y in (-48.0, 48.0):
            t.append(ring(float(x), y, zs))
    t.extend(slots_y(-L / 2.0, 0.0, 6, 30.0, zs))
    return t


def engraved_door_panel(open_pose):
    plate = bd.Box(b.DOOR_LEN, b.DOOR_W, b.DOOR_T).translate((-b.DOOR_LEN / 2.0, 0.0, 0.0))
    tools = door_tools()
    stats = {"removed_mm3": round(removed(plate, tools), 2), "expected_mm3": round(expected(tools), 2)}
    solid = engrave(plate, tools, "b2d_door_panel", b.DOOR_COLOR)
    if open_pose:
        solid = solid.rotate(bd.Axis.Y, b.DOOR_OPEN_DEG)
    solid = solid.translate((b.DOOR_HINGE[0], 0.0, b.DOOR_HINGE[1]))
    solid.label, solid.color = "b2d_door_panel", b.DOOR_COLOR
    return solid, stats


# ---------------------------------------------------------------------------- ramp underside
def ramp_tools():
    zs = -86.0
    t = [rect_ring(-935.0, -312.0, -50.0, 50.0, zs)]
    t.append(seam_y(0.0, -930.0, -316.0, zs))
    for x in (-800.0, -650.0, -500.0, -400.0):
        t.append(seam_x(x, -49.6, 49.6, zs))
    for x in range(-915, -329, -65):
        for y in (-44.0, 44.0):
            t.append(ring(float(x), y, zs))
    for y in (-25.0, 25.0):
        t.extend(slots_x(-725.0, y, 5, 40.0, zs))
    return t


def engraved_ramp(deg):
    stowed = aft._read_parts("Stowed")["intake_r1_ramp"]
    tools = ramp_tools()
    stats = {"removed_mm3": round(removed(stowed, tools), 2), "expected_mm3": round(expected(tools), 2)}
    solid = engrave(stowed, tools, "intake_r1_ramp", stowed.color)
    solid = solid.rotate(bd.Axis((d.HINGE_X, 0.0, d.HINGE_Z), (0, 1, 0)), deg)
    solid.label, solid.color = "intake_r1_ramp", stowed.color
    return solid, stats


# ------------------------------------------------------------------ belly surround of the opening
def belly_tools():
    zs = -86.0
    x0, x1, hw = -972.0, 66.0, 75.5
    t = [rect_ring(x0, x1, -hw, hw, zs)]
    for x in range(-950, 41, 60):
        for y in (-71.0, 71.0):
            t.append(ring(float(x), y, zs))
    for y in (-30.0, 0.0, 30.0):
        t.append(ring(-967.0, y, zs))
        t.append(ring(61.0, y, zs))
    return t


# -------------------------------------------------------------------- engine intake face frame
def engraved_face_frame(deg):
    xs = d.XF + 3.0                          # front plane of the frame (faces +X)
    frame = aft.ruled_loft(((d.XF, b.ENGINE_W, b.ENGINE_H, d.Z_C, 10.0), (xs, b.ENGINE_W, b.ENGINE_H, d.Z_C, 10.0))) - \
        aft.ruled_loft(((d.XF - 1, 96.0, 76.0, d.Z_C, 8.0), (xs + 1.0, 96.0, 76.0, d.Z_C, 8.0)))
    h = DEPTH + OVER
    tools = []
    for yy in (-52.0, 0.0, 52.0):
        for zz in (-41.5, 41.5):
            if yy == 0.0 or True:
                tools.append(ring_x(xs, yy, d.Z_C + zz, h))
    for yy in (-52.0, 52.0):
        tools.append(ring_x(xs, yy, d.Z_C, h))
    stats = {"removed_mm3": round(removed(frame, tools), 2), "expected_mm3": round(expected(tools), 2)}
    solid = d.pose(engrave(frame, tools, "b2d_face_frame", d.PANEL), deg)
    solid.label, solid.color = "b2d_face_frame", d.PANEL
    return solid, stats


def ring_x(xs, cy, cz, h):
    tool = bd.Cylinder(RING_OUT, h) - bd.Cylinder(RING_IN, h + 1.0)
    tool = tool.rotate(bd.Axis.Y, 90.0)  # cylinder axis Z -> X
    return tool.translate((xs + (OVER - DEPTH) / 2.0, cy, cz))


# ---------------------------------------------------------------------------------- assembly
def full(state):
    deg = d.RAMP_DEG if state == "Deployed" else 0.0
    parts = d.read_state(state)
    body = (parts[aft.BODY_LABEL] - d.cutters()).clean()
    btools = belly_tools()
    stats = {"belly": {"removed_mm3": round(removed(body, btools), 2), "expected_mm3": round(expected(btools), 2)}}
    body = engrave(body, btools, aft.BODY_LABEL, parts[aft.BODY_LABEL].color)
    ramp, stats["ramp"] = engraved_ramp(deg)
    door_panel, stats["door"] = engraved_door_panel(state == "Deployed")
    frame, stats["face_frame"] = engraved_face_frame(deg)
    out = [body] + [p for k, p in parts.items() if k not in (aft.BODY_LABEL, "intake_r1_ramp")] + [ramp, aft.liner()]
    for p in d.detail_parts(state):
        if p.label == "b2d_door_panel":
            out.append(door_panel)
        elif p.label == "b2d_face_frame":
            out.append(frame)
        else:
            out.append(p)
    full.stats = stats
    return bd.Compound(children=out, label=f"S_EngineBay_B2F_{state}_Full")


@step(out="../STEP/S_EngineBay_B2F_Deployed_Full.step")
def deployed_full():
    return full("Deployed")


@step(out="../STEP/S_EngineBay_B2F_Stowed_Full.step")
def stowed_full():
    return full("Stowed")


if __name__ == "__main__":
    import json
    deployed_full()
    s1 = getattr(full, 'stats', None)
    stowed_full()
    s2 = getattr(full, 'stats', None)
    (ROOT / "reviews" / "engine_bay_b2f_engraving.json").write_text(json.dumps({"Deployed": s1, "Stowed": s2}, indent=1))
    print(json.dumps({"Deployed": s1, "Stowed": s2}))
