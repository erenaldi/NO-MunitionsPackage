"""Rough concept study B1: engine fixed in the ramp bay, face forward, second forward-hinged door.

Visual concept only (no airflow/thermal/propulsion claim). Builds on the R1 passage and the
approved 35 mm main ramp deployment. The R1 files are untouched; the review context clips the
saved Deployed R1 assembly and adds an *unapproved* forward pocket to the clipped body for viewing.
Coordinates: mm, +X forward, +Y starboard, +Z dorsal.
"""

from __future__ import annotations

import math
from pathlib import Path

from cadgen import build123d as bd, read_step, srgb, step

import aft_exhaust_r1 as aft
import engine_read_study as e

ROOT = Path(__file__).resolve().parents[1]

AXIS_Z = -52.5                 # engine axis = original intake-stub centre line
BAY_X = (-961.0, -295.0)       # existing ramp bay (measured: void X-600/-320/-300, Y<=62, Z-90..-26)
BAY_Z = (-86.0, -26.0)         # belly to ceiling (ceiling is between -26 and -22)
BAY_HALF_Y = 62.0
POCKET_X = (-295.0, -185.0)    # proposed forward extension that houses the second door
DOOR_LEN, DOOR_W, DOOR_T = 100.0, 116.0, 3.0
DOOR_HINGE_X = -190.0
DOOR_OPEN_DEG = 34.0
ENGINE_R = 22.0
STEEL = e.METAL
DOOR_COLOR = srgb("#6d7f8f")


def pocket_cutter():
    """Forward bay extension (same 124 x 60 section as the bay) that the door swings into."""
    box = bd.Box(POCKET_X[1] - POCKET_X[0], 2 * BAY_HALF_Y, BAY_Z[1] - BAY_Z[0] + 4.0)
    return box.translate(((POCKET_X[0] + POCKET_X[1]) / 2.0, 0.0, (BAY_Z[0] - 2.0 + BAY_Z[1]) / 2.0))


def engine_parts():
    L = e.label
    parts = []
    z = AXIS_Z
    # compressor face, inlet lip, spinner
    parts.append(L(e.rotor(-312.0, ENGINE_R, 6.0, 20, 6.0, z=z, ring=False), "b1_fan", e.BLADE))
    lip = e.cyl_x(-324.0, -304.0, 24.5, 0.0, z) - e.cyl_x(-325.0, -303.0, 22.9, 0.0, z)
    parts.append(L(lip.clean(), "b1_inlet_lip", e.METAL))
    parts.append(L(e._cone(-309.0, -294.0, 6.0, 1.0, 0.0, z), "b1_spinner", e.METAL))
    # engine body sections
    parts.append(L(e.cyl_x(-450.0, -324.0, 23.0, 0.0, z), "b1_compressor_casing", e.METAL))
    parts.append(L(e.cyl_x(-720.0, -450.0, 22.0, 0.0, z), "b1_combustor_can", e.METAL))
    parts.append(L(e.cyl_x(-810.0, -720.0, 21.0, 0.0, z), "b1_turbine_casing", e.METAL))
    for k, x in enumerate((-346.0, -372.0, -398.0, -424.0, -500.0, -580.0, -660.0, -765.0)):
        r = 23.0 if x > -450.0 else (22.0 if x > -720.0 else 21.0)
        ring = e.cyl_x(x - 4.0, x + 4.0, r + 1.4, 0.0, z) - e.cyl_x(x - 5.0, x + 5.0, r - 0.5, 0.0, z)
        parts.append(L(ring.clean(), f"b1_band_{k}", e.DARK))
    # ceiling pylons (embed into the bay ceiling as attachment stand-ins)
    for x in (-400.0, -600.0, -780.0):
        r = 23.0 if x > -450.0 else (22.0 if x > -720.0 else 21.0)
        parts.append(L(e.strut_across(x, 0.0, z + r - 1.0, 0.0, BAY_Z[1], 3.0, 9.0, 3.5), f"b1_pylon_{int(-x)}", e.DARK))
    # tailpipe following the R1 connector to the liner
    stations = ((-800.0, z, 20.0), (-953.0, z, 20.0), (-1030.0, z, 19.5), (-1150.0, -35.0, 19.0), (-1270.0, -10.0, 18.0), (-1317.0, 0.0, 17.0))
    loops = [bd.Wire.make_circle(r, bd.Plane(origin=(x, 0.0, cz), z_dir=(1, 0, 0))) for x, cz, r in stations]
    parts.append(L(bd.Solid.make_loft(loops, ruled=True), "b1_tailpipe", e.METAL))
    for x in (-1240.0, -1110.0, -900.0):
        w, h, cz = e.duct_at(x) if x <= -1030.0 else (116.0, 49.0, z)
        for ang in (0, 90, 180, 270):
            dy, dz = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            parts.append(L(e.strut_across(x, dy * 16.0, cz + dz * 16.0, dy * (w / 2.0 if dy else 0.0), cz + dz * (h / 2.0 if dz else 0.0), 2.4, 6.0, 1.5), f"b1_pipe_strut_{int(-x)}_{ang}", e.DARK))
    # afterburner diffuser, spray ring, tail cone, nozzle petals (aft end)
    diff = e._cone(-1317.0, -1350.0, 17.0, 34.0, 0.0, 0.0) - e._cone(-1316.0, -1351.0, 15.8, 32.8, 0.0, 0.0)
    parts.append(L(diff.clean(), "b1_diffuser", e.HOT))
    parts.append(L(e.cyl_x(-1352.0, -1347.0, 34.0) - e.cyl_x(-1353.0, -1346.0, 31.0), "b1_spray_ring", e.DARK))
    for i in range(6):
        sp = bd.Pos(-1349.5, 18.0, 0.0) * bd.Box(4.0, 26.0, 1.6)
        parts.append(L(sp.rotate(bd.Axis.X, 60.0 * i), f"b1_spray_spoke_{i}", e.DARK))
    parts.append(L(e._cone(-1345.0, -1372.0, 8.0, 1.0, 0.0, 0.0), "b1_tail_cone", e.HOT))
    for i, p in enumerate(e.petals_round(-1391.0, -1356.0, 52.0, 44.0, 12)):
        parts.append(L(p, f"b1_nozzle_petal_{i}", e.METAL))
    return parts


def door_part(open_pose: bool):
    """Second ramp: 100 x 116 x 3 plate hinged at its forward edge (axis at mid-thickness); open pose swings the aft edge into the pocket."""
    plate = bd.Box(DOOR_LEN, DOOR_W, DOOR_T).translate((-DOOR_LEN / 2.0, 0.0, 0.0))  # aft of hinge axis, centred on it in Z
    for sy in (-1, 1):  # round hinge knuckles on the axis (rotation-invariant envelope)
        knuckle = bd.Cylinder(2.5, 6.0, rotation=(90, 0, 0)).translate((0.0, sy * (DOOR_W / 2.0 + 1.0), 0.0))
        plate = plate + knuckle
    plate = plate.clean()
    if open_pose:
        plate = plate.rotate(bd.Axis.Y, DOOR_OPEN_DEG)  # +Y rotation lifts the aft (-X) edge
    plate = plate.translate((DOOR_HINGE_X, 0.0, BAY_Z[0] + DOOR_T / 2.0))
    plate.label = "b1_door_open" if open_pose else "b1_door_closed"
    plate.color = DOOR_COLOR
    return plate


def context_leaves(with_pocket: bool):
    """Clip the saved Deployed R1 assembly to a review half-section (Y>=0, X-1400..-100)."""
    source = read_step(str(ROOT / "STEP" / "S_AftExhaust_R1_Deployed.step"))
    clip = bd.Box(1300.0, 500.0, 400.0).translate((-750.0, 250.0, 0.0))
    keep = ("RDM9_R7_symmetric_body", "aft_exhaust_r1_liner", "intake_r1_ramp", "tail_r4", "intake_r1_fixed", "intake_r1_throughpin")
    pieces = []

    def visit(n):
        c = list(getattr(n, "children", ()) or ())
        if c:
            for k in c:
                visit(k)
            return
        if not any(str(n.label).startswith(k) for k in keep):
            return
        common = n & clip
        if common is None or common.volume <= 1e-4:
            return
        if str(n.label).startswith("RDM9") and with_pocket:
            common = (common - pocket_cutter()).clean()
        common.label = str(n.label) + "_SECTION_REVIEW_ONLY"
        common.color = n.color
        pieces.append(common)

    visit(source)
    return pieces


def composite(open_pose: bool):
    return bd.Compound(children=context_leaves(True) + engine_parts() + [door_part(open_pose)],
                       label="S_EngineBay_B1_DoorOpen" if open_pose else "S_EngineBay_B1_DoorClosed")


@step(out="../STEP/S_EngineBay_B1_Engine.step")
def b1_engine():
    return bd.Compound(children=engine_parts(), label="EngineBay_B1_Engine")


@step(out="../STEP/S_EngineBay_B1_DoorOpen_Context.step")
def b1_open():
    return composite(True)


@step(out="../STEP/S_EngineBay_B1_DoorClosed_Context.step")
def b1_closed():
    return composite(False)


if __name__ == "__main__":
    b1_engine()
    b1_open()
    b1_closed()
